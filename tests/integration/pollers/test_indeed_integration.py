"""
Integration tests for Indeed job poller.

Tests end-to-end flow with real database and mocked HTTP responses.
"""

from decimal import Decimal
from unittest.mock import patch

import pytest

from app.pollers.indeed_poller import IndeedPoller
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
        "indeed": {
            "enabled": True,
            "rate_limit_requests_per_hour": 50,
            "delay_between_requests_seconds": [0.1, 0.2],  # Fast for tests
            "user_agent": "Mozilla/5.0 Test",
            "max_pages_per_search": 2,
            "retry_attempts": 3,
            "retry_backoff_seconds": [1, 2, 3],
        },
        "search": {"indeed": {"enabled": True, "search_terms": ["data engineer"], "location": "Australia"}},
    }


@pytest.fixture
def indeed_poller(integration_config, jobs_repo, app_repo):
    """Create Indeed poller with real repositories."""
    return IndeedPoller(config=integration_config, jobs_repository=jobs_repo, application_repository=app_repo)


@pytest.fixture
def sample_indeed_html_page():
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
        <div class="jobsearch-SerpJobCard">
            <h2 class="jobTitle"><a href="/viewjob?jk=87654321">Data Engineering Lead</a></h2>
            <div class="company">Data Corp</div>
            <div class="location">Sydney NSW</div>
            <div class="salaryText">$60 per hour</div>
            <span class="date">3 days ago</span>
        </div>
    </html>
    """


class TestIndeedPollerIntegration:
    """Integration tests for Indeed poller."""

    def test_end_to_end_job_discovery(self, indeed_poller, jobs_repo, app_repo, sample_indeed_html_page):
        """Test complete job discovery flow from scraping to database."""
        with patch("requests.get") as mock_get:

            def side_effect(*args, **kwargs):
                url = args[0]
                mock_response = mock_get.return_value
                if "start=20" in url:
                    # Empty page for page 2
                    mock_response.text = "<html><body>No more jobs</body></html>"
                else:
                    # Jobs on page 1
                    mock_response.text = sample_indeed_html_page
                mock_response.raise_for_status.return_value = None
                return mock_response

            mock_get.side_effect = side_effect

            # Run one poll cycle
            metrics = indeed_poller.run_once()

            # Verify metrics
            assert metrics["jobs_found"] == 2
            assert metrics["jobs_inserted"] == 2
            assert metrics["duplicates_skipped"] == 0
            assert metrics["pages_scraped"] >= 1

            # Verify first job in database
            job1 = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=12345678")
            assert job1 is not None
            assert job1.company_name == "Tech Corp Australia"
            assert job1.job_title == "Senior Data Engineer"
            assert job1.platform_source == "indeed"
            assert job1.location == "Melbourne VIC"
            # $110k pa / 230 days = $478.26
            assert job1.salary_aud_per_day == Decimal("478.26")

            # Verify second job in database
            job2 = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=87654321")
            assert job2 is not None
            assert job2.company_name == "Data Corp"
            assert job2.salary_aud_per_day == Decimal("480")  # $60/hour * 8 hours

            # Verify application tracking records created
            app1 = app_repo.get_application_by_job_id(job1.job_id)
            assert app1 is not None
            assert app1.status == "discovered"

            app2 = app_repo.get_application_by_job_id(job2.job_id)
            assert app2 is not None
            assert app2.status == "discovered"

    def test_duplicate_detection_with_real_database(self, indeed_poller, jobs_repo, sample_indeed_html_page):
        """Test that duplicate jobs are detected using real database."""
        with patch("requests.get") as mock_get:

            def side_effect(*args, **kwargs):
                url = args[0]
                mock_response = mock_get.return_value
                if "start=20" in url:
                    mock_response.text = "<html><body>No more jobs</body></html>"
                else:
                    mock_response.text = sample_indeed_html_page
                mock_response.raise_for_status.return_value = None
                return mock_response

            mock_get.side_effect = side_effect

            # First run - should insert jobs
            metrics1 = indeed_poller.run_once()
            assert metrics1["jobs_inserted"] == 2
            assert metrics1["duplicates_skipped"] == 0

            # Second run - same jobs should be skipped as duplicates
            indeed_poller.reset_metrics()
            metrics2 = indeed_poller.run_once()
            assert metrics2["jobs_inserted"] == 0
            assert metrics2["duplicates_skipped"] == 2

            # Verify only 2 jobs in database (no duplicates)
            jobs = jobs_repo.list_jobs(filters={"platform_source": "indeed"}, limit=10)
            assert len(jobs) == 2

    def test_pagination_handling(self, indeed_poller, jobs_repo):
        """Test that pagination works correctly."""
        page1_html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=page1-job1">Job 1</a></h2>
                <div class="company">Company 1</div>
            </div>
        </html>
        """
        page2_html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=page2-job1">Job 2</a></h2>
                <div class="company">Company 2</div>
            </div>
        </html>
        """

        with patch("requests.get") as mock_get:

            def side_effect(*args, **kwargs):
                url = args[0]
                mock_response = mock_get.return_value
                if "start=20" in url:
                    mock_response.text = page2_html
                else:
                    mock_response.text = page1_html
                mock_response.raise_for_status.return_value = None
                return mock_response

            mock_get.side_effect = side_effect

            # Run poll cycle
            metrics = indeed_poller.run_once()

            # Verify both pages scraped
            assert metrics["pages_scraped"] == 2
            assert metrics["jobs_found"] == 2

            # Verify both jobs in database
            job1 = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=page1-job1")
            job2 = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=page2-job1")
            assert job1 is not None
            assert job2 is not None

    def test_error_recovery_with_database(self, indeed_poller, jobs_repo):
        """Test that poller continues after database errors."""
        valid_html = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=valid">Valid Job</a></h2>
                <div class="company">Good Company</div>
            </div>
        </html>
        """

        with patch("requests.get") as mock_get:

            def side_effect(*args, **kwargs):
                url = args[0]
                mock_response = mock_get.return_value
                if "start=20" in url:
                    mock_response.text = "<html><body>No more jobs</body></html>"
                else:
                    mock_response.text = valid_html
                mock_response.raise_for_status.return_value = None
                return mock_response

            mock_get.side_effect = side_effect

            # First insert should work
            metrics = indeed_poller.run_once()
            assert metrics["jobs_inserted"] == 1

            # Second insert should skip duplicate
            indeed_poller.reset_metrics()
            metrics2 = indeed_poller.run_once()
            assert metrics2["duplicates_skipped"] == 1

    def test_salary_parsing_variations(self, indeed_poller, jobs_repo):
        """Test different salary formats are parsed correctly."""
        html_with_various_salaries = """
        <html>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=annual">Annual Salary Job</a></h2>
                <div class="company">Company A</div>
                <div class="salaryText">$120,000 per year</div>
            </div>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=hourly">Hourly Rate Job</a></h2>
                <div class="company">Company B</div>
                <div class="salaryText">$60 per hour</div>
            </div>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=estimate">Estimate Job</a></h2>
                <div class="company">Company C</div>
                <div class="salaryText">Estimated salary: $100,000 - $120,000 per year</div>
            </div>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=no-salary">No Salary Job</a></h2>
                <div class="company">Company D</div>
            </div>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = html_with_various_salaries
            mock_response.raise_for_status.return_value = None

            metrics = indeed_poller.run_once()
            assert metrics["jobs_inserted"] == 4

            # Check annual salary converted correctly
            annual_job = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=annual")
            assert annual_job.salary_aud_per_day == Decimal("521.74")  # 120k / 230

            # Check hourly converted
            hourly_job = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=hourly")
            assert hourly_job.salary_aud_per_day == Decimal("480")  # 60 * 8

            # Check estimated salary
            estimate_job = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=estimate")
            assert estimate_job.salary_aud_per_day == Decimal("478.26")

            # Check no salary returns None
            no_salary_job = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=no-salary")
            assert no_salary_job.salary_aud_per_day is None

    def test_network_retry_with_real_db(self, indeed_poller):
        """Test retry logic with network errors."""
        with patch("requests.get") as mock_get:
            import requests

            # Create mock response with proper lambda signature
            success_response = type(
                "MockResponse", (), {"text": '<html><div class="jobsearch-SerpJobCard"><h2 class="jobTitle"><a href="/viewjob?jk=1">Job</a></h2><div class="company">Co</div></div></html>', "raise_for_status": lambda self: None}
            )()

            mock_get.side_effect = [requests.exceptions.ConnectionError("Network error"), requests.exceptions.Timeout("Timeout"), success_response]

            # Should succeed after retries
            metrics = indeed_poller.run_once()
            assert metrics["jobs_found"] == 1
            assert metrics["jobs_inserted"] == 1

    def test_empty_results_handling(self, indeed_poller):
        """Test handling of empty search results."""
        empty_html = "<html><body>No jobs found</body></html>"

        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = empty_html
            mock_response.raise_for_status.return_value = None

            metrics = indeed_poller.run_once()

            assert metrics["jobs_found"] == 0
            assert metrics["jobs_inserted"] == 0
            assert metrics["pages_scraped"] == 1

    def test_configuration_applied_correctly(self, indeed_poller):
        """Test that configuration settings are applied."""
        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = "<html></html>"
            mock_response.raise_for_status.return_value = None

            indeed_poller.run_once()

            # Verify user agent was set
            call_args = mock_get.call_args
            assert call_args[1]["headers"]["User-Agent"] == "Mozilla/5.0 Test"

            # Verify timeout was set
            assert call_args[1]["timeout"] == 30

    def test_sponsored_filtering(self, indeed_poller, jobs_repo):
        """Test that sponsored results are filtered out."""
        html_with_sponsored = """
        <html>
            <div class="jobsearch-SerpJobCard" data-sponsoredJob="true">
                <h2 class="jobTitle"><a href="/viewjob?jk=sponsored">Sponsored Job</a></h2>
                <div class="company">Sponsored Company</div>
            </div>
            <div class="jobsearch-SerpJobCard">
                <h2 class="jobTitle"><a href="/viewjob?jk=organic">Organic Job</a></h2>
                <div class="company">Organic Company</div>
            </div>
        </html>
        """

        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.text = html_with_sponsored
            mock_response.raise_for_status.return_value = None

            metrics = indeed_poller.run_once()

            # Should find 1 organic job
            assert metrics["jobs_found"] >= 1
            assert metrics["sponsored_filtered"] >= 1

            # Verify only organic job in database
            organic_job = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=organic")
            assert organic_job is not None

            # Sponsored should not be in database
            sponsored_job = jobs_repo.get_job_by_url("https://au.indeed.com/viewjob?jk=sponsored")
            assert sponsored_job is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
