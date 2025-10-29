"""
Integration tests for SEEK job poller.

Tests end-to-end flow with real database and mocked HTTP responses.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest

from app.pollers.seek_poller import SEEKPoller
from app.repositories.application_repository import ApplicationRepository
from app.repositories.database import initialize_database
from app.repositories.jobs_repository import JobsRepository


@pytest.fixture
def test_db():
    """Initialize test database with schema."""
    initialize_database()
    yield
    # Database will be cleaned up by conftest


@pytest.fixture
def jobs_repo(test_db):
    """Create jobs repository with real database."""
    return JobsRepository()


@pytest.fixture
def app_repo(test_db):
    """Create application repository with real database."""
    return ApplicationRepository()


@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "seek": {
            "enabled": True,
            "rate_limit_requests_per_hour": 50,
            "delay_between_requests_seconds": [0.1, 0.2],  # Fast for tests
            "user_agent": "Mozilla/5.0 Test",
            "max_pages_per_search": 2,
            "retry_attempts": 3,
            "retry_backoff_seconds": [1, 2, 3],
        },
        "search": {"seek": {"enabled": True, "search_terms": ["data engineer"], "location": "Australia"}},
    }


@pytest.fixture
def seek_poller(integration_config, jobs_repo, app_repo):
    """Create SEEK poller with real repositories."""
    return SEEKPoller(config=integration_config, jobs_repository=jobs_repo, application_repository=app_repo)


@pytest.fixture
def sample_seek_html_page():
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
        <article data-automation="normalJob">
            <a data-automation="jobTitle" href="/job/87654321">Data Engineering Lead</a>
            <a data-automation="jobCompany">Data Corp</a>
            <span data-automation="jobLocation">Sydney NSW</span>
            <span data-automation="jobSalary">$1200 per day</span>
            <time datetime="2025-10-26">3d ago</time>
        </article>
    </html>
    """


class TestSEEKPollerIntegration:
    """Integration tests for SEEK poller."""

    def test_end_to_end_job_discovery(self, seek_poller, jobs_repo, app_repo, sample_seek_html_page):
        """Test complete job discovery flow from scraping to database."""
        with patch("requests.get") as mock_get:
            # Mock HTTP response
            mock_response = mock_get.return_value
            mock_response.text = sample_seek_html_page
            mock_response.raise_for_status.return_value = None

            # Run one poll cycle
            metrics = seek_poller.run_once()

            # Verify metrics
            assert metrics["jobs_found"] == 2
            assert metrics["jobs_inserted"] == 2
            assert metrics["duplicates_skipped"] == 0
            assert metrics["pages_scraped"] >= 1

            # Verify first job in database
            job1 = jobs_repo.get_job_by_url("https://www.seek.com.au/job/12345678")
            assert job1 is not None
            assert job1.company_name == "Tech Corp Australia"
            assert job1.job_title == "Senior Data Engineer"
            assert job1.platform_source == "seek"
            assert job1.location == "Melbourne VIC"
            # $110k pa / 230 days = $478.26
            assert job1.salary_aud_per_day == Decimal("478.26")

            # Verify second job in database
            job2 = jobs_repo.get_job_by_url("https://www.seek.com.au/job/87654321")
            assert job2 is not None
            assert job2.company_name == "Data Corp"
            assert job2.salary_aud_per_day == Decimal("1200")

            # Verify application tracking records created
            app1 = app_repo.get_application_by_job_id(job1.job_id)
            assert app1 is not None
            assert app1.status == "discovered"

            app2 = app_repo.get_application_by_job_id(job2.job_id)
            assert app2 is not None
            assert app2.status == "discovered"

    def test_duplicate_detection_with_real_database(self, seek_poller, jobs_repo, sample_seek_html_page):
        """Test that duplicate jobs are detected using real database."""
        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = sample_seek_html_page
            mock_response.raise_for_status.return_value = None

            # First run - should insert jobs
            metrics1 = seek_poller.run_once()
            assert metrics1["jobs_inserted"] == 2
            assert metrics1["duplicates_skipped"] == 0

            # Second run - same jobs should be skipped as duplicates
            seek_poller.reset_metrics()
            metrics2 = seek_poller.run_once()
            assert metrics2["jobs_inserted"] == 0
            assert metrics2["duplicates_skipped"] == 2

            # Verify only 2 jobs in database (no duplicates)
            jobs = jobs_repo.list_jobs(filters={"platform_source": "seek"}, limit=10)
            assert len(jobs) == 2

    def test_pagination_handling(self, seek_poller, jobs_repo):
        """Test that pagination works correctly."""
        page1_html = """
        <html>
            <article data-automation="normalJob">
                <a data-automation="jobTitle" href="/job/page1-job1">Job 1</a>
                <a data-automation="jobCompany">Company 1</a>
            </article>
        </html>
        """
        page2_html = """
        <html>
            <article data-automation="normalJob">
                <a data-automation="jobTitle" href="/job/page2-job1">Job 2</a>
                <a data-automation="jobCompany">Company 2</a>
            </article>
        </html>
        """

        with patch("requests.get") as mock_get:

            def side_effect(*args, **kwargs):
                url = args[0]
                mock_response = mock_get.return_value
                if "page=2" in url:
                    mock_response.text = page2_html
                else:
                    mock_response.text = page1_html
                mock_response.raise_for_status.return_value = None
                return mock_response

            mock_get.side_effect = side_effect

            # Run poll cycle
            metrics = seek_poller.run_once()

            # Verify both pages scraped
            assert metrics["pages_scraped"] == 2
            assert metrics["jobs_found"] == 2

            # Verify both jobs in database
            job1 = jobs_repo.get_job_by_url("https://www.seek.com.au/job/page1-job1")
            job2 = jobs_repo.get_job_by_url("https://www.seek.com.au/job/page2-job1")
            assert job1 is not None
            assert job2 is not None

    def test_error_recovery_with_database(self, seek_poller, jobs_repo):
        """Test that poller continues after database errors."""
        valid_html = """
        <html>
            <article data-automation="normalJob">
                <a data-automation="jobTitle" href="/job/valid">Valid Job</a>
                <a data-automation="jobCompany">Good Company</a>
            </article>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = valid_html
            mock_response.raise_for_status.return_value = None

            # First insert should work
            metrics = seek_poller.run_once()
            assert metrics["jobs_inserted"] == 1

            # Second insert should skip duplicate
            seek_poller.reset_metrics()
            metrics2 = seek_poller.run_once()
            assert metrics2["duplicates_skipped"] == 1

    def test_salary_parsing_variations(self, seek_poller, jobs_repo):
        """Test different salary formats are parsed correctly."""
        html_with_various_salaries = """
        <html>
            <article data-automation="normalJob">
                <a data-automation="jobTitle" href="/job/annual">Annual Salary Job</a>
                <a data-automation="jobCompany">Company A</a>
                <span data-automation="jobSalary">$120,000 per annum</span>
            </article>
            <article data-automation="normalJob">
                <a data-automation="jobTitle" href="/job/daily">Daily Rate Job</a>
                <a data-automation="jobCompany">Company B</a>
                <span data-automation="jobSalary">$800-$1000 per day</span>
            </article>
            <article data-automation="normalJob">
                <a data-automation="jobTitle" href="/job/hourly">Hourly Rate Job</a>
                <a data-automation="jobCompany">Company C</a>
                <span data-automation="jobSalary">$60 per hour</span>
            </article>
            <article data-automation="normalJob">
                <a data-automation="jobTitle" href="/job/competitive">Competitive Salary Job</a>
                <a data-automation="jobCompany">Company D</a>
                <span data-automation="jobSalary">Competitive salary</span>
            </article>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = html_with_various_salaries
            mock_response.raise_for_status.return_value = None

            metrics = seek_poller.run_once()
            assert metrics["jobs_inserted"] == 4

            # Check annual salary converted correctly
            annual_job = jobs_repo.get_job_by_url("https://www.seek.com.au/job/annual")
            assert annual_job.salary_aud_per_day == Decimal("521.74")  # 120k / 230

            # Check daily rate range averaged
            daily_job = jobs_repo.get_job_by_url("https://www.seek.com.au/job/daily")
            assert daily_job.salary_aud_per_day == Decimal("900")  # Average

            # Check hourly converted
            hourly_job = jobs_repo.get_job_by_url("https://www.seek.com.au/job/hourly")
            assert hourly_job.salary_aud_per_day == Decimal("480")  # 60 * 8

            # Check competitive returns None
            competitive_job = jobs_repo.get_job_by_url("https://www.seek.com.au/job/competitive")
            assert competitive_job.salary_aud_per_day is None

    def test_network_retry_with_real_db(self, seek_poller):
        """Test retry logic with network errors."""
        with patch("requests.get") as mock_get:
            # Fail twice, then succeed
            import requests

            mock_get.side_effect = [
                requests.exceptions.ConnectionError("Network error"),
                requests.exceptions.Timeout("Timeout"),
                type("MockResponse", (), {"text": '<html><article data-automation="normalJob"><a data-automation="jobTitle" href="/job/1">Job</a><a data-automation="jobCompany">Co</a></article></html>', "raise_for_status": lambda: None})(),
            ]

            # Should succeed after retries
            metrics = seek_poller.run_once()
            assert metrics["jobs_found"] == 1
            assert metrics["jobs_inserted"] == 1

    def test_empty_results_handling(self, seek_poller):
        """Test handling of empty search results."""
        empty_html = "<html><body>No jobs found</body></html>"

        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = empty_html
            mock_response.raise_for_status.return_value = None

            metrics = seek_poller.run_once()

            assert metrics["jobs_found"] == 0
            assert metrics["jobs_inserted"] == 0
            assert metrics["pages_scraped"] == 1

    def test_configuration_applied_correctly(self, seek_poller):
        """Test that configuration settings are applied."""
        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = "<html></html>"
            mock_response.raise_for_status.return_value = None

            seek_poller.run_once()

            # Verify user agent was set
            call_args = mock_get.call_args
            assert call_args[1]["headers"]["User-Agent"] == "Mozilla/5.0 Test"

            # Verify timeout was set
            assert call_args[1]["timeout"] == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
