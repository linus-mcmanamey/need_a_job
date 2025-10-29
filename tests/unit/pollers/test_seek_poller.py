"""
Unit tests for SEEK job poller.

Tests the SEEKPoller class with mocked dependencies.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.models.application import Application
from app.models.job import Job
from app.pollers.linkedin_poller import RateLimiter


class TestSEEKPollerInit:
    """Test SEEKPoller initialization."""

    def test_init_with_valid_config(self, mock_config, mock_jobs_repo, mock_app_repo):
        """Test initialization with valid configuration."""
        from app.pollers.seek_poller import SEEKPoller

        poller = SEEKPoller(config=mock_config, jobs_repository=mock_jobs_repo, application_repository=mock_app_repo)

        assert poller.config == mock_config
        assert poller.jobs_repo == mock_jobs_repo
        assert poller.app_repo == mock_app_repo
        assert isinstance(poller.rate_limiter, RateLimiter)
        assert poller.metrics == {"jobs_found": 0, "jobs_inserted": 0, "duplicates_skipped": 0, "errors": 0, "pages_scraped": 0}


class TestSEEKPollerSalaryParsing:
    """Test SEEK-specific salary parsing."""

    def test_parse_annual_salary_range(self, seek_poller):
        """Test parsing annual salary range."""
        # "$100,000 - $120,000 per annum" -> average daily rate
        result = seek_poller._parse_seek_salary("$100,000 - $120,000 per annum")
        # Average: $110,000 / 230 working days = $478.26/day
        expected = Decimal("110000") / Decimal("230")
        assert result == expected.quantize(Decimal("0.01"))

    def test_parse_annual_salary_single(self, seek_poller):
        """Test parsing single annual salary."""
        result = seek_poller._parse_seek_salary("$100,000 per annum")
        expected = Decimal("100000") / Decimal("230")
        assert result == expected.quantize(Decimal("0.01"))

    def test_parse_daily_rate_range(self, seek_poller):
        """Test parsing daily rate range."""
        result = seek_poller._parse_seek_salary("$1000-$1200 per day")
        expected = Decimal("1100")  # Average
        assert result == expected

    def test_parse_daily_rate_single(self, seek_poller):
        """Test parsing single daily rate."""
        result = seek_poller._parse_seek_salary("$1000 per day")
        expected = Decimal("1000")
        assert result == expected

    def test_parse_hourly_rate_range(self, seek_poller):
        """Test parsing hourly rate range."""
        result = seek_poller._parse_seek_salary("$50-$70 per hour")
        # Average: $60/hour * 8 hours = $480/day
        expected = Decimal("60") * Decimal("8")
        assert result == expected

    def test_parse_hourly_rate_single(self, seek_poller):
        """Test parsing single hourly rate."""
        result = seek_poller._parse_seek_salary("$60 per hour")
        expected = Decimal("60") * Decimal("8")  # 8 hour day
        assert result == expected

    def test_parse_competitive_salary(self, seek_poller):
        """Test parsing 'Competitive salary' returns None."""
        result = seek_poller._parse_seek_salary("Competitive salary")
        assert result is None

    def test_parse_none_salary(self, seek_poller):
        """Test parsing None salary returns None."""
        result = seek_poller._parse_seek_salary(None)
        assert result is None

    def test_parse_invalid_salary(self, seek_poller):
        """Test parsing invalid salary format returns None."""
        result = seek_poller._parse_seek_salary("Not disclosed")
        assert result is None


class TestSEEKPollerJobExtraction:
    """Test job metadata extraction from SEEK HTML."""

    def test_extract_job_metadata_from_card(self, seek_poller, sample_seek_job_card):
        """Test extracting job metadata from SEEK job card."""
        job = seek_poller.extract_job_metadata(sample_seek_job_card)

        assert isinstance(job, Job)
        assert job.company_name == "Tech Corp Australia"
        assert job.job_title == "Senior Data Engineer"
        assert job.job_url == "https://www.seek.com.au/job/12345678"
        assert job.platform_source == "seek"
        assert job.location == "Melbourne VIC"
        assert job.salary_aud_per_day == Decimal("478.26")  # ~$110k pa / 230 days

    def test_extract_job_with_remote_location(self, seek_poller):
        """Test extracting job with remote location format."""
        job_data = {"title": "Data Engineer", "company": "Remote Co", "location": "Remote - VIC", "salary": "$1200 per day", "job_url": "https://www.seek.com.au/job/99999", "posted_date": "2d ago"}

        job = seek_poller.extract_job_metadata(job_data)
        assert job.location == "Remote - VIC"

    def test_extract_job_with_missing_optional_fields(self, seek_poller):
        """Test extraction with only required fields."""
        minimal_job = {"title": "Data Engineer", "company": "Test Company", "job_url": "https://www.seek.com.au/job/999"}

        job = seek_poller.extract_job_metadata(minimal_job)

        assert job.company_name == "Test Company"
        assert job.job_title == "Data Engineer"
        assert job.job_url == "https://www.seek.com.au/job/999"
        assert job.salary_aud_per_day is None
        assert job.location is None


class TestSEEKPollerPostingDateParsing:
    """Test SEEK posting date parsing."""

    def test_parse_days_ago(self, seek_poller):
        """Test parsing '2d ago' format."""
        result = seek_poller._parse_posting_date("2d ago")
        expected = date.today() - __import__("datetime").timedelta(days=2)
        assert result == expected

    def test_parse_weeks_ago(self, seek_poller):
        """Test parsing '1w ago' format."""
        result = seek_poller._parse_posting_date("1w ago")
        expected = date.today() - __import__("datetime").timedelta(weeks=1)
        assert result == expected

    def test_parse_absolute_date(self, seek_poller):
        """Test parsing absolute date format."""
        result = seek_poller._parse_posting_date("15/01/2025")
        expected = date(2025, 1, 15)
        assert result == expected

    def test_parse_invalid_date(self, seek_poller):
        """Test parsing invalid date returns None."""
        result = seek_poller._parse_posting_date("invalid")
        assert result is None


class TestSEEKPollerURLConstruction:
    """Test SEEK search URL construction."""

    def test_build_search_url_basic(self, seek_poller):
        """Test building basic SEEK search URL."""
        url = seek_poller._build_search_url("data engineer", "Australia")

        assert "https://www.seek.com.au" in url
        assert "data-engineer-jobs" in url
        assert "All-Australia" in url

    def test_build_search_url_with_pagination(self, seek_poller):
        """Test building SEEK URL with pagination."""
        url = seek_poller._build_search_url("data engineer", "Australia", page=2)

        assert "page=2" in url

    def test_build_search_url_with_location(self, seek_poller):
        """Test building SEEK URL with specific location."""
        url = seek_poller._build_search_url("data engineer", "Melbourne")

        assert "Melbourne" in url


class TestSEEKPollerDuplicateDetection:
    """Test duplicate job detection."""

    def test_is_duplicate_returns_true_for_existing_url(self, seek_poller, mock_jobs_repo):
        """Test that is_duplicate returns True when job URL exists."""
        existing_job = Job(company_name="Test", job_title="Engineer", job_url="https://www.seek.com.au/job/12345", platform_source="seek")
        mock_jobs_repo.get_job_by_url.return_value = existing_job

        assert seek_poller.is_duplicate("https://www.seek.com.au/job/12345") is True

    def test_is_duplicate_returns_false_for_new_url(self, seek_poller, mock_jobs_repo):
        """Test that is_duplicate returns False for new job URL."""
        mock_jobs_repo.get_job_by_url.return_value = None

        assert seek_poller.is_duplicate("https://www.seek.com.au/job/new-job") is False


class TestSEEKPollerStoreJob:
    """Test job storage operations."""

    def test_store_job_inserts_job_and_creates_application(self, seek_poller, mock_jobs_repo, mock_app_repo):
        """Test that store_job inserts job and creates application record."""
        job = Job(company_name="Test Company", job_title="Data Engineer", job_url="https://www.seek.com.au/job/123", platform_source="seek")

        job_id = seek_poller.store_job(job)

        # Verify job inserted
        mock_jobs_repo.insert_job.assert_called_once_with(job)
        assert job_id == "test-job-id"

        # Verify application created
        mock_app_repo.insert_application.assert_called_once()
        app_call_args = mock_app_repo.insert_application.call_args[0][0]
        assert isinstance(app_call_args, Application)
        assert app_call_args.job_id == "test-job-id"
        assert app_call_args.status == "discovered"


class TestSEEKPollerErrorHandling:
    """Test error handling scenarios."""

    @patch("time.sleep")
    def test_fetch_page_with_retry_succeeds_on_second_attempt(self, mock_sleep, seek_poller):
        """Test retry logic succeeds on second attempt."""
        with patch.object(seek_poller, "_fetch_page") as mock_fetch:
            # Fail once, then succeed
            mock_fetch.side_effect = [ConnectionError("Connection failed"), "<html>Success</html>"]

            html = seek_poller._fetch_page_with_retry("https://test.com")

            assert html == "<html>Success</html>"
            assert mock_fetch.call_count == 2

    @patch("time.sleep")
    def test_fetch_page_with_retry_exhausts_attempts(self, mock_sleep, seek_poller):
        """Test retry logic gives up after max attempts."""
        with patch.object(seek_poller, "_fetch_page") as mock_fetch:
            mock_fetch.side_effect = ConnectionError("Connection failed")

            with pytest.raises(ConnectionError):
                seek_poller._fetch_page_with_retry("https://test.com")

            assert mock_fetch.call_count == 3  # Default max retries


class TestSEEKPollerRunOnce:
    """Test single poll cycle execution."""

    def test_run_once_processes_jobs_successfully(self, seek_poller, mock_jobs_repo, mock_app_repo, sample_seek_html):
        """Test successful execution of one poll cycle."""
        with patch.object(seek_poller, "_fetch_page") as mock_fetch:
            mock_fetch.return_value = sample_seek_html
            mock_jobs_repo.get_job_by_url.return_value = None  # No duplicates

            metrics = seek_poller.run_once()

            # Verify metrics
            assert metrics["jobs_found"] >= 1
            assert metrics["jobs_inserted"] >= 1
            assert metrics["pages_scraped"] >= 1

    def test_run_once_skips_duplicates(self, seek_poller, mock_jobs_repo, sample_seek_html):
        """Test that run_once skips duplicate jobs."""
        with patch.object(seek_poller, "_fetch_page") as mock_fetch:
            mock_fetch.return_value = sample_seek_html

            # Mock job as existing (duplicate)
            existing_job = Job(company_name="Test", job_title="Engineer", job_url="https://www.seek.com.au/job/12345678", platform_source="seek")
            mock_jobs_repo.get_job_by_url.return_value = existing_job

            metrics = seek_poller.run_once()

            # Verify job was not inserted
            mock_jobs_repo.insert_job.assert_not_called()
            assert metrics["duplicates_skipped"] >= 1


class TestSEEKPollerRateLimiting:
    """Test rate limiting behavior."""

    def test_rate_limiter_waits_between_requests(self, seek_poller):
        """Test that poller adds delays between requests."""
        with patch("time.sleep") as mock_sleep:
            with patch("random.uniform") as mock_random:
                mock_random.return_value = 3.0

                seek_poller._add_random_delay()

                mock_sleep.assert_called_once_with(3.0)


# Fixtures


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return {
        "seek": {"enabled": True, "rate_limit_requests_per_hour": 50, "delay_between_requests_seconds": [2, 5], "user_agent": "Mozilla/5.0 (Test)", "max_pages_per_search": 5, "retry_attempts": 3, "retry_backoff_seconds": [5, 15, 45]},
        "search": {"seek": {"enabled": True, "search_terms": ["data engineer"], "location": "Australia"}},
    }


@pytest.fixture
def mock_jobs_repo():
    """Create mock JobsRepository."""
    repo = Mock()
    repo.get_job_by_url = Mock(return_value=None)
    repo.insert_job = Mock(return_value="test-job-id")
    return repo


@pytest.fixture
def mock_app_repo():
    """Create mock ApplicationRepository."""
    repo = Mock()
    repo.insert_application = Mock(return_value="test-app-id")
    return repo


@pytest.fixture
def seek_poller(mock_config, mock_jobs_repo, mock_app_repo):
    """Create SEEKPoller instance with mocked dependencies."""
    from app.pollers.seek_poller import SEEKPoller

    return SEEKPoller(config=mock_config, jobs_repository=mock_jobs_repo, application_repository=mock_app_repo)


@pytest.fixture
def sample_seek_job_card():
    """Sample SEEK job card data."""
    return {"title": "Senior Data Engineer", "company": "Tech Corp Australia", "location": "Melbourne VIC", "salary": "$100,000 - $120,000 per annum", "job_url": "https://www.seek.com.au/job/12345678", "posted_date": "2d ago"}


@pytest.fixture
def sample_seek_html():
    """Sample SEEK search results HTML."""
    return """
    <html>
        <article data-automation="normalJob">
            <a data-automation="jobTitle" href="/job/12345678">Senior Data Engineer</a>
            <a data-automation="jobCompany">Tech Corp Australia</a>
            <span data-automation="jobLocation">Melbourne VIC</span>
            <span data-automation="jobSalary">$100,000 - $120,000 per annum</span>
            <time datetime="2025-10-27">2d ago</time>
        </article>
    </html>
    """


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
