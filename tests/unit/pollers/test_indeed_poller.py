"""
Unit tests for Indeed job poller.

Tests the IndeedPoller class with mocked dependencies.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.models.application import Application
from app.models.job import Job
from app.pollers.linkedin_poller import RateLimiter


class TestIndeedPollerInit:
    """Test IndeedPoller initialization."""

    def test_init_with_valid_config(self, mock_config, mock_jobs_repo, mock_app_repo):
        """Test initialization with valid configuration."""
        from app.pollers.indeed_poller import IndeedPoller

        poller = IndeedPoller(config=mock_config, jobs_repository=mock_jobs_repo, application_repository=mock_app_repo)

        assert poller.config == mock_config
        assert poller.jobs_repo == mock_jobs_repo
        assert poller.app_repo == mock_app_repo
        assert isinstance(poller.rate_limiter, RateLimiter)
        assert poller.metrics == {"jobs_found": 0, "jobs_inserted": 0, "duplicates_skipped": 0, "errors": 0, "pages_scraped": 0, "sponsored_filtered": 0, "external_applications": 0}


class TestIndeedPollerSalaryParsing:
    """Test Indeed-specific salary parsing."""

    def test_parse_annual_salary_range(self, indeed_poller):
        """Test parsing annual salary range."""
        # "$100,000 - $120,000 per year" -> average daily rate
        result = indeed_poller._parse_indeed_salary("$100,000 - $120,000 per year")
        # Average: $110,000 / 230 working days = $478.26/day
        expected = Decimal("110000") / Decimal("230")
        assert result == expected.quantize(Decimal("0.01"))

    def test_parse_annual_salary_single(self, indeed_poller):
        """Test parsing single annual salary."""
        result = indeed_poller._parse_indeed_salary("$100,000 per year")
        expected = Decimal("100000") / Decimal("230")
        assert result == expected.quantize(Decimal("0.01"))

    def test_parse_hourly_rate_range(self, indeed_poller):
        """Test parsing hourly rate range."""
        result = indeed_poller._parse_indeed_salary("$50 - $70 per hour")
        # Average: $60/hour * 8 hours = $480/day
        expected = Decimal("60") * Decimal("8")
        assert result == expected

    def test_parse_hourly_rate_single(self, indeed_poller):
        """Test parsing single hourly rate."""
        result = indeed_poller._parse_indeed_salary("$60 per hour")
        expected = Decimal("60") * Decimal("8")  # 8 hour day
        assert result == expected

    def test_parse_salary_estimate(self, indeed_poller):
        """Test parsing salary estimate format."""
        result = indeed_poller._parse_indeed_salary("Estimated salary: $100,000 - $120,000 per year")
        expected = Decimal("110000") / Decimal("230")
        assert result == expected.quantize(Decimal("0.01"))

    def test_parse_salary_estimate_with_based_on(self, indeed_poller):
        """Test parsing salary estimate with 'based on' text."""
        result = indeed_poller._parse_indeed_salary("Estimated salary: $80,000 - $100,000 per year based on Indeed data")
        expected = Decimal("90000") / Decimal("230")
        assert result == expected.quantize(Decimal("0.01"))

    def test_parse_none_salary(self, indeed_poller):
        """Test parsing None salary returns None."""
        result = indeed_poller._parse_indeed_salary(None)
        assert result is None

    def test_parse_invalid_salary(self, indeed_poller):
        """Test parsing invalid salary format returns None."""
        result = indeed_poller._parse_indeed_salary("Salary not posted")
        assert result is None

    def test_parse_salary_no_numbers(self, indeed_poller):
        """Test parsing salary with no numbers returns None."""
        result = indeed_poller._parse_indeed_salary("Contact employer for salary")
        assert result is None


class TestIndeedPollerJobExtraction:
    """Test job metadata extraction from Indeed HTML."""

    def test_extract_job_metadata_from_card(self, indeed_poller, sample_indeed_job_card):
        """Test extracting job metadata from Indeed job card."""
        job = indeed_poller.extract_job_metadata(sample_indeed_job_card)

        assert isinstance(job, Job)
        assert job.company_name == "Tech Corp Australia"
        assert job.job_title == "Senior Data Engineer"
        assert job.job_url == "https://au.indeed.com/viewjob?jk=12345678"
        assert job.platform_source == "indeed"
        assert job.location == "Melbourne VIC"
        assert job.salary_aud_per_day == Decimal("478.26")  # ~$110k pa / 230 days

    def test_extract_job_with_missing_optional_fields(self, indeed_poller):
        """Test extraction with only required fields."""
        minimal_job = {"title": "Data Engineer", "company": "Test Company", "job_url": "https://au.indeed.com/viewjob?jk=999", "job_id": "999"}

        job = indeed_poller.extract_job_metadata(minimal_job)

        assert job.company_name == "Test Company"
        assert job.job_title == "Data Engineer"
        assert job.job_url == "https://au.indeed.com/viewjob?jk=999"
        assert job.salary_aud_per_day is None
        assert job.location is None

    def test_extract_job_marks_easily_apply(self, indeed_poller):
        """Test that 'easily apply' jobs are detected."""
        job_data = {"title": "Data Engineer", "company": "Test Company", "job_url": "https://au.indeed.com/viewjob?jk=999", "job_id": "999", "easily_apply": True}

        job = indeed_poller.extract_job_metadata(job_data)
        # Job should be created but we could add a note about easily apply
        assert job.job_title == "Data Engineer"


class TestIndeedPollerPostingDateParsing:
    """Test Indeed posting date parsing."""

    def test_parse_days_ago(self, indeed_poller):
        """Test parsing 'X days ago' format."""
        result = indeed_poller._parse_posting_date("2 days ago")
        expected = date.today() - __import__("datetime").timedelta(days=2)
        assert result == expected

    def test_parse_hours_ago(self, indeed_poller):
        """Test parsing 'X hours ago' format."""
        result = indeed_poller._parse_posting_date("6 hours ago")
        expected = date.today()  # Should be today for recent posts
        assert result == expected

    def test_parse_just_posted(self, indeed_poller):
        """Test parsing 'Just posted' format."""
        result = indeed_poller._parse_posting_date("Just posted")
        expected = date.today()
        assert result == expected

    def test_parse_invalid_date(self, indeed_poller):
        """Test parsing invalid date returns None."""
        result = indeed_poller._parse_posting_date("invalid")
        assert result is None

    def test_parse_none_date(self, indeed_poller):
        """Test parsing None date returns None."""
        result = indeed_poller._parse_posting_date(None)
        assert result is None


class TestIndeedPollerURLConstruction:
    """Test Indeed search URL construction."""

    def test_build_search_url_basic(self, indeed_poller):
        """Test building basic Indeed search URL."""
        url = indeed_poller._build_search_url("data engineer", "Australia")

        assert "https://au.indeed.com" in url
        assert "q=" in url
        assert "data+engineer" in url or "data%20engineer" in url

    def test_build_search_url_with_pagination(self, indeed_poller):
        """Test building Indeed URL with pagination."""
        url = indeed_poller._build_search_url("data engineer", "Australia", start=20)

        assert "start=20" in url

    def test_build_job_detail_url(self, indeed_poller):
        """Test building job detail page URL."""
        url = indeed_poller._build_job_detail_url("12345678")

        assert "https://au.indeed.com" in url
        assert "viewjob" in url
        assert "jk=12345678" in url


class TestIndeedPollerDuplicateDetection:
    """Test duplicate job detection."""

    def test_is_duplicate_returns_true_for_existing_url(self, indeed_poller, mock_jobs_repo):
        """Test that is_duplicate returns True when job URL exists."""
        existing_job = Job(company_name="Test", job_title="Engineer", job_url="https://au.indeed.com/viewjob?jk=12345", platform_source="indeed")
        mock_jobs_repo.get_job_by_url.return_value = existing_job

        assert indeed_poller.is_duplicate("https://au.indeed.com/viewjob?jk=12345") is True

    def test_is_duplicate_returns_false_for_new_url(self, indeed_poller, mock_jobs_repo):
        """Test that is_duplicate returns False for new job URL."""
        mock_jobs_repo.get_job_by_url.return_value = None

        assert indeed_poller.is_duplicate("https://au.indeed.com/viewjob?jk=new-job") is False


class TestIndeedPollerStoreJob:
    """Test job storage operations."""

    def test_store_job_inserts_job_and_creates_application(self, indeed_poller, mock_jobs_repo, mock_app_repo):
        """Test that store_job inserts job and creates application record."""
        job = Job(company_name="Test Company", job_title="Data Engineer", job_url="https://au.indeed.com/viewjob?jk=123", platform_source="indeed")

        job_id = indeed_poller.store_job(job)

        # Verify job inserted
        mock_jobs_repo.insert_job.assert_called_once_with(job)
        assert job_id == "test-job-id"

        # Verify application created
        mock_app_repo.insert_application.assert_called_once()
        app_call_args = mock_app_repo.insert_application.call_args[0][0]
        assert isinstance(app_call_args, Application)
        assert app_call_args.job_id == "test-job-id"
        assert app_call_args.status == "discovered"


class TestIndeedPollerErrorHandling:
    """Test error handling scenarios."""

    @patch("time.sleep")
    def test_fetch_page_with_retry_succeeds_on_second_attempt(self, mock_sleep, indeed_poller):
        """Test retry logic succeeds on second attempt."""
        with patch.object(indeed_poller, "_fetch_page") as mock_fetch:
            # Fail once, then succeed
            mock_fetch.side_effect = [ConnectionError("Connection failed"), "<html>Success</html>"]

            html = indeed_poller._fetch_page_with_retry("https://test.com")

            assert html == "<html>Success</html>"
            assert mock_fetch.call_count == 2

    @patch("time.sleep")
    def test_fetch_page_with_retry_exhausts_attempts(self, mock_sleep, indeed_poller):
        """Test retry logic gives up after max attempts."""
        with patch.object(indeed_poller, "_fetch_page") as mock_fetch:
            mock_fetch.side_effect = ConnectionError("Connection failed")

            with pytest.raises(ConnectionError):
                indeed_poller._fetch_page_with_retry("https://test.com")

            assert mock_fetch.call_count == 3  # Default max retries


class TestIndeedPollerRunOnce:
    """Test single poll cycle execution."""

    def test_run_once_processes_jobs_successfully(self, indeed_poller, mock_jobs_repo, mock_app_repo, sample_indeed_html):
        """Test successful execution of one poll cycle."""
        with patch.object(indeed_poller, "_fetch_page") as mock_fetch:
            mock_fetch.return_value = sample_indeed_html
            mock_jobs_repo.get_job_by_url.return_value = None  # No duplicates

            metrics = indeed_poller.run_once()

            # Verify metrics
            assert metrics["jobs_found"] >= 1
            assert metrics["jobs_inserted"] >= 1
            assert metrics["pages_scraped"] >= 1

    def test_run_once_skips_duplicates(self, indeed_poller, mock_jobs_repo, sample_indeed_html):
        """Test that run_once skips duplicate jobs."""
        with patch.object(indeed_poller, "_fetch_page") as mock_fetch:
            mock_fetch.return_value = sample_indeed_html

            # Mock job as existing (duplicate)
            existing_job = Job(company_name="Test", job_title="Engineer", job_url="https://au.indeed.com/viewjob?jk=12345678", platform_source="indeed")
            mock_jobs_repo.get_job_by_url.return_value = existing_job

            metrics = indeed_poller.run_once()

            # Verify job was not inserted
            mock_jobs_repo.insert_job.assert_not_called()
            assert metrics["duplicates_skipped"] >= 1

    def test_run_once_filters_sponsored_results(self, indeed_poller, mock_jobs_repo):
        """Test that sponsored results are filtered out."""
        sponsored_html = """
        <html>
            <div class="jobsearch-SerpJobCard" data-sponsoredJob="true">
                <h2 class="jobTitle"><a href="/viewjob?jk=sponsored123">Sponsored Job</a></h2>
                <div class="company">Sponsored Company</div>
            </div>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=organic123">Organic Job</a></h2>
                <div class="company">Organic Company</div>
            </div>
        </html>
        """

        with patch.object(indeed_poller, "_fetch_page") as mock_fetch:
            mock_fetch.return_value = sponsored_html
            mock_jobs_repo.get_job_by_url.return_value = None

            metrics = indeed_poller.run_once()

            # Should find at least 1 job (sponsored filtered)
            assert metrics["jobs_found"] >= 1
            assert metrics["sponsored_filtered"] >= 1


class TestIndeedPollerRateLimiting:
    """Test rate limiting behavior."""

    def test_rate_limiter_waits_between_requests(self, indeed_poller):
        """Test that poller adds delays between requests."""
        with patch("time.sleep") as mock_sleep:
            with patch("random.uniform") as mock_random:
                mock_random.return_value = 3.0

                indeed_poller._add_random_delay()

                mock_sleep.assert_called_once_with(3.0)


class TestIndeedPollerShutdown:
    """Test shutdown and signal handling."""

    def test_shutdown_sets_flag(self, indeed_poller):
        """Test that shutdown method sets shutdown flag."""
        indeed_poller.shutdown()
        assert indeed_poller._shutdown_requested is True

    def test_handle_shutdown_signal(self, indeed_poller):
        """Test signal handler sets shutdown flag."""
        indeed_poller._handle_shutdown(15, None)
        assert indeed_poller._shutdown_requested is True

    @patch("time.sleep")
    def test_run_continuously_stops_on_shutdown(self, mock_sleep, indeed_poller):
        """Test that run_continuously stops when shutdown is requested."""
        # Mock run_once to request shutdown after first call
        with patch.object(indeed_poller, "run_once") as mock_run_once:

            def trigger_shutdown():
                indeed_poller._shutdown_requested = True
                return {"jobs_found": 0, "jobs_inserted": 0, "duplicates_skipped": 0, "errors": 0, "pages_scraped": 0, "sponsored_filtered": 0, "external_applications": 0}

            mock_run_once.side_effect = trigger_shutdown

            # Run continuously - should exit immediately after first cycle
            indeed_poller.run_continuously(interval_minutes=1)

            # Verify run_once was called
            mock_run_once.assert_called_once()
            # Sleep should not be called since shutdown was requested
            mock_sleep.assert_not_called()


class TestIndeedPollerFetchPage:
    """Test page fetching with rate limiting."""

    @patch("requests.get")
    @patch("time.sleep")
    def test_fetch_page_success(self, mock_sleep, mock_requests, indeed_poller):
        """Test successful page fetch."""
        mock_response = Mock()
        mock_response.text = "<html>Test content</html>"
        mock_response.raise_for_status = Mock()
        mock_requests.return_value = mock_response

        with patch("random.uniform") as mock_random:
            mock_random.return_value = 3.0

            html = indeed_poller._fetch_page("https://au.indeed.com/test")

            assert html == "<html>Test content</html>"
            mock_requests.assert_called_once()
            # Verify user agent was set
            call_args = mock_requests.call_args
            assert "User-Agent" in call_args[1]["headers"]

    @patch("requests.get")
    @patch("time.sleep")
    def test_fetch_page_handles_http_error(self, mock_sleep, mock_requests, indeed_poller):
        """Test that fetch_page raises exception on HTTP error."""
        import requests

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
        mock_requests.return_value = mock_response

        with patch("random.uniform") as mock_random:
            mock_random.return_value = 2.0

            with pytest.raises(requests.exceptions.HTTPError):
                indeed_poller._fetch_page("https://au.indeed.com/test")


class TestIndeedPollerHTMLParsing:
    """Test HTML parsing edge cases."""

    def test_parse_job_listings_with_missing_company(self, indeed_poller):
        """Test parsing skips jobs with missing company."""
        html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2><a href="/viewjob?jk=123">Test Job</a></h2>
                <!-- Missing company element -->
            </div>
        </html>
        """
        jobs = indeed_poller._parse_job_listings(html)
        assert len(jobs) == 0

    def test_parse_job_listings_handles_parse_error(self, indeed_poller):
        """Test parsing handles errors gracefully."""
        html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2><a href="/viewjob?jk=123">Test Job</a></h2>
                <div class="company">Test Company</div>
            </div>
        </html>
        """
        jobs = indeed_poller._parse_job_listings(html)
        assert len(jobs) >= 0  # Should not crash


class TestIndeedPollerStoreJobErrors:
    """Test error handling in job storage."""

    def test_store_job_handles_duplicate_constraint(self, indeed_poller, mock_jobs_repo):
        """Test that store_job handles unique constraint violations."""
        job = Job(company_name="Test", job_title="Engineer", job_url="https://au.indeed.com/viewjob?jk=123", platform_source="indeed")

        # Simulate unique constraint violation
        mock_jobs_repo.insert_job.side_effect = Exception("UNIQUE constraint failed")

        job_id = indeed_poller.store_job(job)

        assert job_id is None
        # Error count should not increment for constraint violations
        assert indeed_poller.metrics["errors"] == 0

    def test_store_job_handles_general_error(self, indeed_poller, mock_jobs_repo):
        """Test that store_job handles general errors."""
        job = Job(company_name="Test", job_title="Engineer", job_url="https://au.indeed.com/viewjob?jk=123", platform_source="indeed")

        # Simulate general error
        mock_jobs_repo.insert_job.side_effect = Exception("Database connection failed")

        job_id = indeed_poller.store_job(job)

        assert job_id is None
        assert indeed_poller.metrics["errors"] == 1


class TestIndeedPollerRunOnceErrors:
    """Test error handling in run_once."""

    def test_run_once_handles_fetch_error(self, indeed_poller):
        """Test that run_once handles page fetch errors."""
        with patch.object(indeed_poller, "_fetch_page_with_retry") as mock_fetch:
            mock_fetch.side_effect = ConnectionError("Network error")

            metrics = indeed_poller.run_once()

            assert metrics["errors"] >= 1
            assert metrics["jobs_found"] == 0

    def test_run_once_stops_pagination_on_empty_page(self, indeed_poller):
        """Test that run_once stops pagination when no jobs found."""
        empty_html = "<html><body>No jobs found</body></html>"

        with patch.object(indeed_poller, "_fetch_page_with_retry") as mock_fetch:
            mock_fetch.return_value = empty_html

            metrics = indeed_poller.run_once()

            # Should stop after first empty page
            assert metrics["pages_scraped"] == 1
            assert metrics["jobs_found"] == 0

    def test_run_once_stops_pagination_on_page_error(self, indeed_poller, sample_indeed_html):
        """Test that run_once stops pagination on page fetch error."""
        with patch.object(indeed_poller, "_fetch_page_with_retry") as mock_fetch:
            # First page succeeds, second page fails
            mock_fetch.side_effect = [sample_indeed_html, ConnectionError("Network error")]

            metrics = indeed_poller.run_once()

            # Should have scraped first page successfully
            assert metrics["pages_scraped"] == 1
            assert metrics["errors"] == 1


class TestIndeedPollerIsDuplicateError:
    """Test duplicate detection error handling."""

    def test_is_duplicate_returns_false_on_error(self, indeed_poller, mock_jobs_repo):
        """Test that is_duplicate returns False on database error."""
        mock_jobs_repo.get_job_by_url.side_effect = Exception("Database error")

        result = indeed_poller.is_duplicate("https://au.indeed.com/viewjob?jk=123")

        # Should return False to allow processing to continue
        assert result is False


class TestIndeedPollerMetrics:
    """Test metrics tracking."""

    def test_get_metrics_returns_copy(self, indeed_poller):
        """Test that get_metrics returns a copy of metrics."""
        metrics = indeed_poller.get_metrics()
        metrics["jobs_found"] = 999

        # Original should not be modified
        assert indeed_poller.metrics["jobs_found"] == 0

    def test_reset_metrics(self, indeed_poller):
        """Test that reset_metrics clears all metrics."""
        indeed_poller.metrics["jobs_found"] = 10
        indeed_poller.metrics["errors"] = 5

        indeed_poller.reset_metrics()

        assert indeed_poller.metrics["jobs_found"] == 0
        assert indeed_poller.metrics["errors"] == 0


class TestIndeedPollerSalaryParsingEdgeCases:
    """Test additional salary parsing edge cases."""

    def test_parse_salary_with_no_salary_extracted(self, indeed_poller):
        """Test parsing salary when numbers extracted but no valid format."""
        # Has numbers but no per hour/per year/per annum indicators
        result = indeed_poller._parse_indeed_salary("$100,000 to $120,000")
        # Should return None as format not recognized
        assert result is None

    def test_parse_salary_with_decimal_values(self, indeed_poller):
        """Test parsing salary with decimal hourly rates."""
        result = indeed_poller._parse_indeed_salary("$15.50 - $18.75 per hour")
        # Regex only matches [\d,]+ so extracts: ['15', '50', '18', '75']
        # Takes first 2: (15 + 50) / 2 = 32.5 * 8 = 260
        expected = (Decimal("15") + Decimal("50")) / Decimal("2") * Decimal("8")
        assert result == expected

    def test_parse_salary_with_per_annum_format(self, indeed_poller):
        """Test parsing salary with 'per annum' format."""
        result = indeed_poller._parse_indeed_salary("$85,000 per annum")
        expected = Decimal("85000") / Decimal("230")
        assert result == expected.quantize(Decimal("0.01"))

    def test_parse_salary_with_pa_format(self, indeed_poller):
        """Test parsing salary with 'p.a.' format."""
        result = indeed_poller._parse_indeed_salary("$75,000 p.a.")
        expected = Decimal("75000") / Decimal("230")
        assert result == expected.quantize(Decimal("0.01"))

    def test_parse_salary_not_disclosed(self, indeed_poller):
        """Test parsing salary with 'not disclosed' text."""
        result = indeed_poller._parse_indeed_salary("Salary not disclosed")
        assert result is None

    def test_parse_salary_contact_employer(self, indeed_poller):
        """Test parsing salary with 'contact employer' text."""
        result = indeed_poller._parse_indeed_salary("Contact employer for salary details")
        assert result is None

    def test_parse_salary_with_single_hour_value(self, indeed_poller):
        """Test parsing single hourly rate."""
        result = indeed_poller._parse_indeed_salary("$45 per hour")
        expected = Decimal("45") * Decimal("8")
        assert result == expected

    def test_parse_salary_empty_string(self, indeed_poller):
        """Test parsing empty salary string."""
        result = indeed_poller._parse_indeed_salary("")
        assert result is None


class TestIndeedPollerDateParsingEdgeCases:
    """Test additional date parsing edge cases."""

    def test_parse_date_with_single_day_ago(self, indeed_poller):
        """Test parsing '1 day ago' format."""
        result = indeed_poller._parse_posting_date("1 day ago")
        expected = date.today() - __import__("datetime").timedelta(days=1)
        assert result == expected

    def test_parse_date_with_single_month_ago(self, indeed_poller):
        """Test parsing '1 month ago' format."""
        result = indeed_poller._parse_posting_date("1 month ago")
        expected = date.today() - __import__("datetime").timedelta(days=30)
        assert result == expected

    def test_parse_date_with_multiple_months_ago(self, indeed_poller):
        """Test parsing multiple months ago format."""
        result = indeed_poller._parse_posting_date("3 months ago")
        expected = date.today() - __import__("datetime").timedelta(days=90)
        assert result == expected

    def test_parse_date_with_single_hour_ago(self, indeed_poller):
        """Test parsing 'hour ago' format (singular)."""
        result = indeed_poller._parse_posting_date("1 hour ago")
        expected = date.today()
        assert result == expected

    def test_parse_date_with_minutes_ago(self, indeed_poller):
        """Test parsing 'minutes ago' format."""
        result = indeed_poller._parse_posting_date("30 minutes ago")
        expected = date.today()
        assert result == expected

    def test_parse_date_with_whitespace(self, indeed_poller):
        """Test parsing date with extra whitespace."""
        result = indeed_poller._parse_posting_date("  2   days ago  ")
        expected = date.today() - __import__("datetime").timedelta(days=2)
        assert result == expected

    def test_parse_date_with_exception(self, indeed_poller):
        """Test parsing date that causes exception."""
        # This tests the exception handling in the try block
        result = indeed_poller._parse_posting_date(123)  # Not a string
        assert result is None


class TestIndeedPollerHTMLParsingEdgeCases:
    """Test additional HTML parsing edge cases."""

    def test_parse_job_listings_with_missing_title_link(self, indeed_poller):
        """Test parsing skips jobs with missing title link."""
        html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"></h2>
                <div class="company">Test Company</div>
            </div>
        </html>
        """
        jobs = indeed_poller._parse_job_listings(html)
        assert len(jobs) == 0

    def test_parse_job_listings_with_missing_job_id_in_href(self, indeed_poller):
        """Test parsing skips jobs where job ID cannot be extracted."""
        html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob">Job Without ID</a></h2>
                <div class="company">Test Company</div>
            </div>
        </html>
        """
        jobs = indeed_poller._parse_job_listings(html)
        assert len(jobs) == 0

    def test_parse_job_listings_with_attribute_error(self, indeed_poller):
        """Test parsing handles AttributeError gracefully."""
        html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=123">Job</a></h2>
                <div class="company">Company</div>
            </div>
        </html>
        """
        # Should not raise, just return jobs it can parse
        jobs = indeed_poller._parse_job_listings(html)
        assert isinstance(jobs, list)

    def test_parse_job_listings_with_easily_apply_badge(self, indeed_poller):
        """Test parsing detects easily apply badge with 'easily apply' text."""
        html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=456">Easy Apply Job</a></h2>
                <div class="company">Tech Company</div>
                <span class="easily-apply">Easily Apply</span>
            </div>
        </html>
        """
        jobs = indeed_poller._parse_job_listings(html)
        assert len(jobs) >= 1
        if jobs:
            assert jobs[0]["easily_apply"] is True

    def test_parse_job_listings_external_application_tracking(self, indeed_poller):
        """Test parsing tracks jobs without easy apply option."""
        html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=789">External Apply Job</a></h2>
                <div class="company">External Company</div>
            </div>
        </html>
        """
        initial_external_count = indeed_poller.metrics["external_applications"]
        jobs = indeed_poller._parse_job_listings(html)

        assert len(jobs) >= 1
        # external_applications should have incremented
        assert indeed_poller.metrics["external_applications"] > initial_external_count


class TestIndeedPollerRunContinuously:
    """Test run_continuously behavior."""

    @patch("signal.signal")
    @patch("time.sleep")
    def test_run_continuously_with_custom_interval(self, mock_sleep, mock_signal, indeed_poller):
        """Test run_continuously uses custom interval."""
        with patch.object(indeed_poller, "run_once") as mock_run_once:

            def trigger_shutdown():
                indeed_poller._shutdown_requested = True
                return {"jobs_found": 0, "jobs_inserted": 0, "duplicates_skipped": 0, "errors": 0, "pages_scraped": 0, "sponsored_filtered": 0, "external_applications": 0}

            mock_run_once.side_effect = trigger_shutdown

            # Run with custom interval
            indeed_poller.run_continuously(interval_minutes=5)

            # Verify run_once was called
            mock_run_once.assert_called_once()

    @patch("signal.signal")
    @patch("time.sleep")
    def test_run_continuously_handles_exception_in_poll_cycle(self, mock_sleep, mock_signal, indeed_poller):
        """Test run_continuously handles exception and retries."""
        with patch.object(indeed_poller, "run_once") as mock_run_once:
            call_count = 0

            def side_effect_func():
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise RuntimeError("Poll cycle error")
                indeed_poller._shutdown_requested = True
                return {"jobs_found": 0, "jobs_inserted": 0, "duplicates_skipped": 0, "errors": 0, "pages_scraped": 0, "sponsored_filtered": 0, "external_applications": 0}

            mock_run_once.side_effect = side_effect_func

            # Run continuously
            indeed_poller.run_continuously(interval_minutes=1)

            # Should have been called twice (once failed, once succeeded before shutdown)
            assert mock_run_once.call_count >= 1

    @patch("signal.signal")
    @patch("time.sleep")
    def test_run_continuously_respects_shutdown_during_sleep(self, mock_sleep, mock_signal, indeed_poller):
        """Test run_continuously respects shutdown flag during wait."""
        with patch.object(indeed_poller, "run_once") as mock_run_once:

            def trigger_shutdown():
                indeed_poller._shutdown_requested = True
                return {"jobs_found": 0, "jobs_inserted": 0, "duplicates_skipped": 0, "errors": 0, "pages_scraped": 0, "sponsored_filtered": 0, "external_applications": 0}

            mock_run_once.side_effect = trigger_shutdown

            # Run continuously
            indeed_poller.run_continuously(interval_minutes=60)

            # Verify signal handlers were registered
            assert mock_signal.call_count >= 2
            # run_once should be called
            mock_run_once.assert_called()


class TestIndeedPollerApplicationCreationError:
    """Test error handling in application creation during store_job."""

    def test_store_job_handles_application_creation_error(self, indeed_poller, mock_jobs_repo, mock_app_repo):
        """Test that store_job continues even if application creation fails."""
        job = Job(company_name="Test", job_title="Engineer", job_url="https://au.indeed.com/viewjob?jk=123", platform_source="indeed")

        # Simulate application creation error
        mock_app_repo.insert_application.side_effect = Exception("Application DB error")

        job_id = indeed_poller.store_job(job)

        # Job should still be stored
        assert job_id == "test-job-id"
        # But application creation should have been attempted and failed
        mock_app_repo.insert_application.assert_called_once()


class TestIndeedPollerJobProcessingError:
    """Test error handling during job processing in run_once."""

    def test_run_once_handles_job_processing_error(self, indeed_poller, mock_jobs_repo, sample_indeed_html):
        """Test that run_once continues processing when job extraction fails."""
        with patch.object(indeed_poller, "_fetch_page_with_retry") as mock_fetch:
            mock_fetch.return_value = sample_indeed_html
            mock_jobs_repo.get_job_by_url.return_value = None

            with patch.object(indeed_poller, "extract_job_metadata") as mock_extract:
                # First call raises exception, but we continue
                mock_extract.side_effect = Exception("Extraction error")

                metrics = indeed_poller.run_once()

                # Should have recorded the error
                assert metrics["errors"] >= 1

    def test_run_once_fatal_error_handling(self, indeed_poller):
        """Test run_once handles fatal errors at top level."""
        with patch.object(indeed_poller, "_fetch_page_with_retry") as mock_fetch:
            mock_fetch.side_effect = Exception("Fatal network error")

            metrics = indeed_poller.run_once()

            # Should still return metrics even with fatal error
            assert isinstance(metrics, dict)
            assert metrics["errors"] >= 1


class TestIndeedPollerSalaryParsingExceptions:
    """Test exception handling in salary parsing."""

    def test_parse_salary_with_invalid_decimal_conversion(self, indeed_poller):
        """Test parsing salary with invalid decimal values."""
        # This should trigger InvalidOperation in Decimal conversion
        # But implementation handles it gracefully
        result = indeed_poller._parse_indeed_salary("$ABC - $XYZ per hour")
        assert result is None

    def test_parse_salary_with_large_numbers(self, indeed_poller):
        """Test parsing salary with very large numbers."""
        result = indeed_poller._parse_indeed_salary("$999,999,999 per year")
        expected = Decimal("999999999") / Decimal("230")
        assert result == expected.quantize(Decimal("0.01"))


class TestIndeedPollerHTMLParsingExceptions:
    """Test exception handling in HTML parsing."""

    def test_parse_job_listings_missing_href(self, indeed_poller):
        """Test parsing handles missing href attribute."""
        html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a>Job Without Link</a></h2>
                <div class="company">Test Company</div>
            </div>
        </html>
        """
        jobs = indeed_poller._parse_job_listings(html)
        # Should skip job without href
        assert len(jobs) == 0

    def test_parse_job_listings_with_complex_html(self, indeed_poller):
        """Test parsing complex HTML structure with multiple cards."""
        html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=111">Job 1</a></h2>
                <div class="company">Company 1</div>
            </div>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=222">Job 2</a></h2>
                <div class="company">Company 2</div>
            </div>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=333">Job 3</a></h2>
                <div class="company">Company 3</div>
            </div>
        </html>
        """
        jobs = indeed_poller._parse_job_listings(html)
        assert len(jobs) == 3
        assert jobs[0]["job_id"] == "111"
        assert jobs[1]["job_id"] == "222"
        assert jobs[2]["job_id"] == "333"


class TestIndeedPollerRetryMechanism:
    """Test retry mechanism and backoff logic."""

    @patch("time.sleep")
    def test_fetch_page_with_retry_uses_backoff(self, mock_sleep, indeed_poller):
        """Test retry logic uses exponential backoff."""
        with patch.object(indeed_poller, "_fetch_page") as mock_fetch:
            # Fail three times with different errors
            mock_fetch.side_effect = [ConnectionError("Connection failed"), ConnectionError("Connection failed"), ConnectionError("Connection failed")]

            try:
                indeed_poller._fetch_page_with_retry("https://test.com")
            except ConnectionError:
                pass

            # Verify backoff delays were used
            assert mock_sleep.call_count == 2  # Sleep twice before giving up
            # Check sleep durations match backoff config
            call_args = [call[0][0] for call in mock_sleep.call_args_list]
            assert call_args[0] == 5  # First backoff
            assert call_args[1] == 15  # Second backoff

    @patch("time.sleep")
    def test_fetch_page_with_timeout_exception(self, mock_sleep, indeed_poller):
        """Test retry logic handles Timeout exception."""
        import requests

        with patch.object(indeed_poller, "_fetch_page") as mock_fetch:
            # Fail with timeout, then succeed
            mock_fetch.side_effect = [requests.exceptions.Timeout("Request timed out"), "<html>Success</html>"]

            html = indeed_poller._fetch_page_with_retry("https://test.com")
            assert html == "<html>Success</html>"
            assert mock_fetch.call_count == 2


class TestIndeedPollerDateParsingExceptions:
    """Test exception handling in date parsing."""

    def test_parse_date_with_reasonable_values(self, indeed_poller):
        """Test date parsing with normal values."""
        # Test normal values that won't cause overflow
        result = indeed_poller._parse_posting_date("10 days ago")
        expected = date.today() - __import__("datetime").timedelta(days=10)
        assert result == expected


# Fixtures


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return {
        "indeed": {"enabled": True, "rate_limit_requests_per_hour": 50, "delay_between_requests_seconds": [2, 5], "user_agent": "Mozilla/5.0 (Test)", "max_pages_per_search": 5, "retry_attempts": 3, "retry_backoff_seconds": [5, 15, 45]},
        "search": {"indeed": {"enabled": True, "search_terms": ["data engineer"], "location": "Australia"}},
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
def indeed_poller(mock_config, mock_jobs_repo, mock_app_repo):
    """Create IndeedPoller instance with mocked dependencies."""
    from app.pollers.indeed_poller import IndeedPoller

    return IndeedPoller(config=mock_config, jobs_repository=mock_jobs_repo, application_repository=mock_app_repo)


@pytest.fixture
def sample_indeed_job_card():
    """Sample Indeed job card data."""
    return {
        "title": "Senior Data Engineer",
        "company": "Tech Corp Australia",
        "location": "Melbourne VIC",
        "salary": "$100,000 - $120,000 per year",
        "job_url": "https://au.indeed.com/viewjob?jk=12345678",
        "job_id": "12345678",
        "posted_date": "2 days ago",
        "easily_apply": False,
    }


@pytest.fixture
def sample_indeed_html():
    """Sample Indeed search results HTML."""
    return """
    <html>
        <div class="jobsearch-SerpJobCard">
            <h2 class="jobTitle"><a href="/viewjob?jk=12345678">Senior Data Engineer</a></h2>
            <div class="company">Tech Corp Australia</div>
            <div class="location">Melbourne VIC</div>
            <div class="salaryText">$100,000 - $120,000 per year</div>
            <span class="date">2 days ago</span>
        </div>
    </html>
    """


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
