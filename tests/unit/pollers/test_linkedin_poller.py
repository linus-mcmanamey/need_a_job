"""
Unit tests for LinkedIn job poller.

Tests the LinkedInPoller class with mocked dependencies.
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from app.models.application import Application
from app.models.job import Job
from app.pollers.linkedin_poller import LinkedInPoller, RateLimiter


class TestRateLimiter:
    """Test the RateLimiter utility class."""

    def test_rate_limiter_allows_calls_under_limit(self):
        """Test that rate limiter allows calls under the limit."""
        limiter = RateLimiter(calls_per_hour=100)

        # Should not wait for first call
        with patch("time.sleep") as mock_sleep:
            limiter.wait_if_needed()
            mock_sleep.assert_not_called()

    def test_rate_limiter_waits_when_limit_reached(self):
        """Test that rate limiter waits when limit is reached."""
        limiter = RateLimiter(calls_per_hour=2)

        # Make 2 calls (at limit)
        limiter.wait_if_needed()
        limiter.wait_if_needed()

        # Third call should wait
        with patch("time.sleep") as mock_sleep:
            limiter.wait_if_needed()
            mock_sleep.assert_called_once()

    def test_rate_limiter_clears_old_calls(self):
        """Test that rate limiter clears calls older than 1 hour."""
        limiter = RateLimiter(calls_per_hour=2)

        # Add old call (more than 1 hour ago)
        old_time = datetime.now().timestamp() - 3700  # 1 hour + 100s ago
        limiter.calls = [datetime.fromtimestamp(old_time)]

        # Should allow call without waiting (old call cleared)
        with patch("time.sleep") as mock_sleep:
            limiter.wait_if_needed()
            mock_sleep.assert_not_called()


@pytest.fixture
def mock_config():
    """Create mock configuration."""
    return {
        "linkedin": {"polling_interval_minutes": 60, "rate_limit_requests_per_minute": 10, "timeout_seconds": 30, "search_filters": {"location": "Australia", "job_type": "Contract", "remote": True}},
        "search": {"keywords": {"primary": ["Data Engineer", "Senior Data Engineer"], "secondary": ["Analytics Engineer"]}, "locations": {"primary": "Remote (Australia-wide)"}, "job_type": "contract"},
    }


@pytest.fixture
def mock_jobs_repo():
    """Create mock JobsRepository."""
    repo = Mock()
    repo.get_job_by_url = Mock(return_value=None)  # No duplicates by default
    repo.insert_job = Mock(return_value="test-job-id")
    return repo


@pytest.fixture
def mock_app_repo():
    """Create mock ApplicationRepository."""
    repo = Mock()
    repo.insert_application = Mock(return_value="test-app-id")
    return repo


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client."""
    client = Mock()
    return client


@pytest.fixture
def linkedin_poller(mock_config, mock_jobs_repo, mock_app_repo, mock_mcp_client):
    """Create LinkedInPoller instance with mocked dependencies."""
    return LinkedInPoller(config=mock_config, jobs_repository=mock_jobs_repo, application_repository=mock_app_repo, mcp_client=mock_mcp_client)


@pytest.fixture
def sample_linkedin_job():
    """Sample LinkedIn job response from MCP server."""
    return {
        "job_id": "linkedin-123",
        "title": "Senior Data Engineer",
        "company": "Tech Corp",
        "location": "Remote - Australia",
        "posted_date": "2025-01-15",
        "salary": "$1000-$1200/day",
        "job_url": "https://linkedin.com/jobs/view/12345",
        "description": "We are looking for a Senior Data Engineer to join our team...",
        "requirements": "Python, SQL, Cloud platforms (Azure/AWS/GCP)",
        "responsibilities": "Design and build data pipelines, mentor junior engineers",
    }


class TestLinkedInPollerInit:
    """Test LinkedInPoller initialization."""

    def test_init_with_valid_config(self, mock_config, mock_jobs_repo, mock_app_repo, mock_mcp_client):
        """Test initialization with valid configuration."""
        poller = LinkedInPoller(config=mock_config, jobs_repository=mock_jobs_repo, application_repository=mock_app_repo, mcp_client=mock_mcp_client)

        assert poller.config == mock_config
        assert poller.jobs_repo == mock_jobs_repo
        assert poller.app_repo == mock_app_repo
        assert poller.mcp_client == mock_mcp_client
        assert isinstance(poller.rate_limiter, RateLimiter)
        assert poller.metrics == {"jobs_found": 0, "jobs_inserted": 0, "duplicates_skipped": 0, "errors": 0}


class TestLinkedInPollerJobExtraction:
    """Test job metadata extraction from LinkedIn responses."""

    def test_extract_job_metadata_with_complete_data(self, linkedin_poller, sample_linkedin_job):
        """Test extracting job metadata with all fields present."""
        job = linkedin_poller.extract_job_metadata(sample_linkedin_job)

        assert isinstance(job, Job)
        assert job.company_name == "Tech Corp"
        assert job.job_title == "Senior Data Engineer"
        assert job.job_url == "https://linkedin.com/jobs/view/12345"
        assert job.platform_source == "linkedin"
        assert job.location == "Remote - Australia"
        assert job.posted_date == date(2025, 1, 15)
        assert job.job_description == sample_linkedin_job["description"]
        assert job.requirements == sample_linkedin_job["requirements"]
        assert job.responsibilities == sample_linkedin_job["responsibilities"]

    def test_extract_job_metadata_parses_salary(self, linkedin_poller):
        """Test salary parsing from various formats."""
        # Test daily rate range
        job_data = {"title": "Engineer", "company": "Test Co", "job_url": "https://test.com/job", "salary": "$1000-$1200/day", "posted_date": "2025-01-15"}
        job = linkedin_poller.extract_job_metadata(job_data)
        assert job.salary_aud_per_day == Decimal("1100.00")  # Average

        # Test single rate
        job_data["salary"] = "$1000/day"
        job = linkedin_poller.extract_job_metadata(job_data)
        assert job.salary_aud_per_day == Decimal("1000.00")

        # Test no salary
        job_data["salary"] = None
        job = linkedin_poller.extract_job_metadata(job_data)
        assert job.salary_aud_per_day is None

    def test_extract_job_metadata_with_missing_optional_fields(self, linkedin_poller):
        """Test extraction with only required fields."""
        minimal_job = {"title": "Data Engineer", "company": "Test Company", "job_url": "https://linkedin.com/jobs/view/999", "posted_date": "2025-01-15"}

        job = linkedin_poller.extract_job_metadata(minimal_job)

        assert job.company_name == "Test Company"
        assert job.job_title == "Data Engineer"
        assert job.job_url == "https://linkedin.com/jobs/view/999"
        assert job.salary_aud_per_day is None
        assert job.location is None
        assert job.job_description is None

    def test_extract_job_metadata_handles_invalid_date(self, linkedin_poller):
        """Test handling of invalid posted_date."""
        job_data = {"title": "Engineer", "company": "Test Co", "job_url": "https://test.com/job", "posted_date": "invalid-date"}

        job = linkedin_poller.extract_job_metadata(job_data)
        assert job.posted_date is None


class TestLinkedInPollerDuplicateDetection:
    """Test duplicate job detection."""

    def test_is_duplicate_returns_true_for_existing_url(self, linkedin_poller, mock_jobs_repo):
        """Test that is_duplicate returns True when job URL exists."""
        existing_job = Job(company_name="Test", job_title="Engineer", job_url="https://linkedin.com/jobs/view/12345", platform_source="linkedin")
        mock_jobs_repo.get_job_by_url.return_value = existing_job

        assert linkedin_poller.is_duplicate("https://linkedin.com/jobs/view/12345") is True
        mock_jobs_repo.get_job_by_url.assert_called_once_with("https://linkedin.com/jobs/view/12345")

    def test_is_duplicate_returns_false_for_new_url(self, linkedin_poller, mock_jobs_repo):
        """Test that is_duplicate returns False for new job URL."""
        mock_jobs_repo.get_job_by_url.return_value = None

        assert linkedin_poller.is_duplicate("https://linkedin.com/jobs/view/new-job") is False

    def test_is_duplicate_handles_repository_error(self, linkedin_poller, mock_jobs_repo):
        """Test that is_duplicate handles database errors gracefully."""
        mock_jobs_repo.get_job_by_url.side_effect = Exception("Database error")

        # Should return False and log error rather than crash
        assert linkedin_poller.is_duplicate("https://test.com/job") is False


class TestLinkedInPollerStoreJob:
    """Test job storage operations."""

    def test_store_job_inserts_job_and_creates_application(self, linkedin_poller, mock_jobs_repo, mock_app_repo):
        """Test that store_job inserts job and creates application record."""
        job = Job(company_name="Test Company", job_title="Data Engineer", job_url="https://linkedin.com/jobs/view/123", platform_source="linkedin")

        job_id = linkedin_poller.store_job(job)

        # Verify job inserted
        mock_jobs_repo.insert_job.assert_called_once_with(job)
        assert job_id == "test-job-id"

        # Verify application created
        mock_app_repo.insert_application.assert_called_once()
        app_call_args = mock_app_repo.insert_application.call_args[0][0]
        assert isinstance(app_call_args, Application)
        assert app_call_args.job_id == "test-job-id"
        assert app_call_args.status == "discovered"

    def test_store_job_handles_duplicate_constraint_error(self, linkedin_poller, mock_jobs_repo, mock_app_repo):
        """Test handling of duplicate constraint violations."""
        job = Job(company_name="Test", job_title="Engineer", job_url="https://test.com/job", platform_source="linkedin")

        mock_jobs_repo.insert_job.side_effect = Exception("Constraint violation: job_url")

        job_id = linkedin_poller.store_job(job)

        # Should return None and not create application
        assert job_id is None
        mock_app_repo.insert_application.assert_not_called()

    def test_store_job_handles_application_creation_error(self, linkedin_poller, mock_jobs_repo, mock_app_repo):
        """Test handling of application creation errors."""
        job = Job(company_name="Test", job_title="Engineer", job_url="https://test.com/job", platform_source="linkedin")

        mock_app_repo.insert_application.side_effect = Exception("Database error")

        # Should still return job_id even if application creation fails
        job_id = linkedin_poller.store_job(job)
        assert job_id == "test-job-id"


class TestLinkedInPollerSearchJobs:
    """Test LinkedIn job search via MCP server."""

    def test_search_jobs_calls_mcp_with_correct_params(self, linkedin_poller, mock_mcp_client, sample_linkedin_job):
        """Test that search_jobs calls MCP server with correct parameters."""
        mock_mcp_client.call_tool.return_value = {"jobs": [sample_linkedin_job], "total_results": 1}

        results = linkedin_poller.search_jobs(keywords=["Data Engineer"], location="Australia", job_type="contract")

        # Verify MCP call
        mock_mcp_client.call_tool.assert_called_once()
        call_args = mock_mcp_client.call_tool.call_args
        assert call_args[0][0] == "mcp__linkedin__search_jobs"

        params = call_args[1]["params"]
        assert "Data Engineer" in params["query"]
        assert params["location"] == "Australia"
        assert params["job_type"] == "contract"

        # Verify results
        assert len(results) == 1
        assert results[0] == sample_linkedin_job

    def test_search_jobs_handles_mcp_connection_error(self, linkedin_poller, mock_mcp_client):
        """Test handling of MCP server connection errors."""
        mock_mcp_client.call_tool.side_effect = ConnectionError("MCP server unavailable")

        # search_jobs should raise the exception for retry logic to handle
        with pytest.raises(ConnectionError):
            linkedin_poller.search_jobs(keywords=["Data Engineer"])

    def test_search_jobs_handles_rate_limit_error(self, linkedin_poller, mock_mcp_client):
        """Test handling of rate limit errors from LinkedIn."""
        mock_mcp_client.call_tool.side_effect = Exception("Rate limit exceeded")

        # search_jobs should raise the exception for retry logic to handle
        with pytest.raises(Exception):
            linkedin_poller.search_jobs(keywords=["Data Engineer"])

    def test_search_jobs_handles_invalid_response(self, linkedin_poller, mock_mcp_client):
        """Test handling of invalid response format from MCP."""
        mock_mcp_client.call_tool.return_value = {"error": "Invalid request"}

        results = linkedin_poller.search_jobs(keywords=["Data Engineer"])

        assert results == []


class TestLinkedInPollerRunOnce:
    """Test single poll cycle execution."""

    def test_run_once_processes_jobs_successfully(self, linkedin_poller, mock_mcp_client, mock_jobs_repo, mock_app_repo, sample_linkedin_job):
        """Test successful execution of one poll cycle."""
        mock_mcp_client.call_tool.return_value = {"jobs": [sample_linkedin_job], "total_results": 1}
        mock_jobs_repo.get_job_by_url.return_value = None  # No duplicates

        metrics = linkedin_poller.run_once()

        # Verify search was called
        mock_mcp_client.call_tool.assert_called()

        # Verify job was stored
        mock_jobs_repo.insert_job.assert_called_once()
        mock_app_repo.insert_application.assert_called_once()

        # Verify metrics
        assert metrics["jobs_found"] == 1
        assert metrics["jobs_inserted"] == 1
        assert metrics["duplicates_skipped"] == 0
        assert metrics["errors"] == 0

    def test_run_once_skips_duplicates(self, linkedin_poller, mock_mcp_client, mock_jobs_repo, sample_linkedin_job):
        """Test that run_once skips duplicate jobs."""
        mock_mcp_client.call_tool.return_value = {"jobs": [sample_linkedin_job], "total_results": 1}

        # Mock job as existing (duplicate)
        existing_job = Job(company_name="Test", job_title="Engineer", job_url=sample_linkedin_job["job_url"], platform_source="linkedin")
        mock_jobs_repo.get_job_by_url.return_value = existing_job

        metrics = linkedin_poller.run_once()

        # Verify job was not inserted
        mock_jobs_repo.insert_job.assert_not_called()

        # Verify metrics
        assert metrics["jobs_found"] == 1
        assert metrics["jobs_inserted"] == 0
        assert metrics["duplicates_skipped"] == 1

    def test_run_once_processes_multiple_jobs(self, linkedin_poller, mock_mcp_client, mock_jobs_repo, mock_app_repo):
        """Test processing multiple jobs in one cycle."""
        jobs = [{"title": f"Engineer {i}", "company": f"Company {i}", "job_url": f"https://linkedin.com/jobs/view/{i}", "posted_date": "2025-01-15"} for i in range(5)]

        mock_mcp_client.call_tool.return_value = {"jobs": jobs, "total_results": 5}
        mock_jobs_repo.get_job_by_url.return_value = None

        metrics = linkedin_poller.run_once()

        assert metrics["jobs_found"] == 5
        assert metrics["jobs_inserted"] == 5
        assert mock_jobs_repo.insert_job.call_count == 5

    def test_run_once_continues_after_individual_job_error(self, linkedin_poller, mock_mcp_client, mock_jobs_repo, mock_app_repo):
        """Test that run_once continues processing after individual job errors."""
        jobs = [{"title": "Job 1", "company": "Co 1", "job_url": "https://test.com/1", "posted_date": "2025-01-15"}, {"title": "Job 2", "company": "Co 2", "job_url": "https://test.com/2", "posted_date": "2025-01-15"}]

        mock_mcp_client.call_tool.return_value = {"jobs": jobs, "total_results": 2}

        # Both jobs are not duplicates
        mock_jobs_repo.get_job_by_url.return_value = None

        # First job fails on insert, second succeeds
        mock_jobs_repo.insert_job.side_effect = [Exception("Database error"), "job-2-id"]

        metrics = linkedin_poller.run_once()

        # Should still process second job
        assert metrics["jobs_found"] == 2
        assert metrics["jobs_inserted"] == 1
        assert metrics["errors"] == 1


class TestLinkedInPollerRetryLogic:
    """Test retry logic with exponential backoff."""

    @patch("time.sleep")
    def test_search_retries_on_connection_error(self, mock_sleep, linkedin_poller, mock_mcp_client, sample_linkedin_job):
        """Test that search retries on connection errors."""
        # Fail twice, then succeed
        mock_mcp_client.call_tool.side_effect = [ConnectionError("Connection failed"), ConnectionError("Connection failed"), {"jobs": [sample_linkedin_job], "total_results": 1}]

        results = linkedin_poller.search_jobs_with_retry(keywords=["Data Engineer"])

        # Should succeed on third attempt
        assert len(results) == 1
        assert mock_mcp_client.call_tool.call_count == 3

        # Verify exponential backoff
        assert mock_sleep.call_count == 2

    @patch("time.sleep")
    def test_search_gives_up_after_max_retries(self, mock_sleep, linkedin_poller, mock_mcp_client):
        """Test that search gives up after max retry attempts."""
        mock_mcp_client.call_tool.side_effect = ConnectionError("Connection failed")

        results = linkedin_poller.search_jobs_with_retry(keywords=["Data Engineer"], max_retries=3)

        assert results == []
        assert mock_mcp_client.call_tool.call_count == 3


class TestLinkedInPollerMetrics:
    """Test metrics collection and reporting."""

    def test_get_metrics_returns_current_state(self, linkedin_poller):
        """Test that get_metrics returns current metrics."""
        linkedin_poller.metrics["jobs_found"] = 10
        linkedin_poller.metrics["jobs_inserted"] = 8
        linkedin_poller.metrics["duplicates_skipped"] = 2

        metrics = linkedin_poller.get_metrics()

        assert metrics["jobs_found"] == 10
        assert metrics["jobs_inserted"] == 8
        assert metrics["duplicates_skipped"] == 2

    def test_reset_metrics_clears_counters(self, linkedin_poller):
        """Test that reset_metrics clears all counters."""
        linkedin_poller.metrics["jobs_found"] = 10
        linkedin_poller.metrics["errors"] = 5

        linkedin_poller.reset_metrics()

        assert linkedin_poller.metrics["jobs_found"] == 0
        assert linkedin_poller.metrics["jobs_inserted"] == 0
        assert linkedin_poller.metrics["duplicates_skipped"] == 0
        assert linkedin_poller.metrics["errors"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
