"""
Integration tests for LinkedIn job poller.

Tests end-to-end flow with real database and mocked MCP server.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from app.models.job import Job
from app.pollers.linkedin_poller import LinkedInPoller
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
def mock_mcp_client():
    """Create mock MCP client."""
    return Mock()


@pytest.fixture
def integration_config():
    """Configuration for integration tests."""
    return {
        "linkedin": {
            "polling_interval_minutes": 60,
            "rate_limit_requests_per_minute": 10,
            "timeout_seconds": 30,
            "search_filters": {"location": "Australia", "job_type": "Contract", "remote": True},
        },
        "search": {
            "keywords": {"primary": ["Data Engineer"], "secondary": ["Analytics Engineer"]},
            "locations": {"primary": "Remote (Australia-wide)"},
            "job_type": "contract",
        },
    }


@pytest.fixture
def linkedin_poller(integration_config, jobs_repo, app_repo, mock_mcp_client):
    """Create LinkedIn poller with real repositories and mocked MCP."""
    return LinkedInPoller(
        config=integration_config,
        jobs_repository=jobs_repo,
        application_repository=app_repo,
        mcp_client=mock_mcp_client,
    )


class TestLinkedInPollerIntegration:
    """Integration tests for LinkedIn poller."""

    def test_end_to_end_job_discovery(self, linkedin_poller, jobs_repo, app_repo, mock_mcp_client):
        """Test complete job discovery flow from MCP to database."""
        # Mock MCP response
        mock_jobs = [
            {
                "job_id": "linkedin-123",
                "title": "Senior Data Engineer",
                "company": "Tech Corp",
                "location": "Remote - Australia",
                "posted_date": "2025-01-15",
                "salary": "$1000-$1200/day",
                "job_url": "https://linkedin.com/jobs/view/12345",
                "description": "Looking for a senior data engineer...",
                "requirements": "Python, SQL, Cloud",
                "responsibilities": "Build data pipelines",
            }
        ]
        mock_mcp_client.call_tool.return_value = {"jobs": mock_jobs, "total_results": 1}

        # Run one poll cycle
        metrics = linkedin_poller.run_once()

        # Verify metrics
        assert metrics["jobs_found"] == 1
        assert metrics["jobs_inserted"] == 1
        assert metrics["duplicates_skipped"] == 0
        assert metrics["errors"] == 0

        # Verify job in database
        job = jobs_repo.get_job_by_url("https://linkedin.com/jobs/view/12345")
        assert job is not None
        assert job.company_name == "Tech Corp"
        assert job.job_title == "Senior Data Engineer"
        assert job.platform_source == "linkedin"
        assert job.salary_aud_per_day == Decimal("1100.00")  # Average of range

        # Verify application tracking record created
        application = app_repo.get_application_by_job_id(job.job_id)
        assert application is not None
        assert application.status == "discovered"
        assert application.current_stage is None

    def test_duplicate_detection_with_real_database(
        self, linkedin_poller, jobs_repo, mock_mcp_client
    ):
        """Test that duplicate jobs are detected using real database."""
        # Mock MCP response with same job twice
        mock_job = {
            "title": "Data Engineer",
            "company": "Test Company",
            "job_url": "https://linkedin.com/jobs/view/999",
            "posted_date": "2025-01-15",
            "salary": "$1000/day",
        }
        mock_mcp_client.call_tool.return_value = {"jobs": [mock_job], "total_results": 1}

        # First run - should insert job
        metrics1 = linkedin_poller.run_once()
        assert metrics1["jobs_inserted"] == 1
        assert metrics1["duplicates_skipped"] == 0

        # Second run - same job should be skipped as duplicate
        linkedin_poller.reset_metrics()
        metrics2 = linkedin_poller.run_once()
        assert metrics2["jobs_inserted"] == 0
        assert metrics2["duplicates_skipped"] == 1

        # Verify only one job in database
        jobs = jobs_repo.list_jobs(filters={"job_url": "https://linkedin.com/jobs/view/999"})
        assert len(jobs) == 1

    def test_multiple_jobs_batch_processing(
        self, linkedin_poller, jobs_repo, app_repo, mock_mcp_client
    ):
        """Test processing multiple jobs in one poll cycle."""
        # Mock MCP response with multiple jobs
        mock_jobs = [
            {
                "title": f"Data Engineer {i}",
                "company": f"Company {i}",
                "job_url": f"https://linkedin.com/jobs/view/{i}",
                "posted_date": "2025-01-15",
                "salary": f"${1000 + i * 100}/day",
            }
            for i in range(5)
        ]
        mock_mcp_client.call_tool.return_value = {"jobs": mock_jobs, "total_results": 5}

        # Run poll cycle
        metrics = linkedin_poller.run_once()

        # Verify all jobs processed
        assert metrics["jobs_found"] == 5
        assert metrics["jobs_inserted"] == 5
        assert metrics["errors"] == 0

        # Verify jobs in database
        jobs = jobs_repo.list_jobs(filters={"platform_source": "linkedin"}, limit=10)
        assert len(jobs) == 5

        # Verify each job has application tracking
        for job in jobs:
            app = app_repo.get_application_by_job_id(job.job_id)
            assert app is not None
            assert app.status == "discovered"

    def test_partial_failure_handling(self, linkedin_poller, jobs_repo, mock_mcp_client):
        """Test that poller continues when some jobs fail to process."""
        # Mock MCP response
        mock_jobs = [
            {
                "title": "Valid Job",
                "company": "Good Company",
                "job_url": "https://linkedin.com/jobs/view/valid",
                "posted_date": "2025-01-15",
            },
            {
                "title": "Job with Invalid Date",
                "company": "Another Company",
                "job_url": "https://linkedin.com/jobs/view/invalid",
                "posted_date": "not-a-date",
            },
            {
                "title": "Another Valid Job",
                "company": "Third Company",
                "job_url": "https://linkedin.com/jobs/view/valid2",
                "posted_date": "2025-01-16",
            },
        ]
        mock_mcp_client.call_tool.return_value = {"jobs": mock_jobs, "total_results": 3}

        # Run poll cycle
        metrics = linkedin_poller.run_once()

        # All jobs should be processed (invalid date handled gracefully)
        assert metrics["jobs_found"] == 3
        assert metrics["jobs_inserted"] == 3  # Invalid date is handled, job still inserted

        # Verify valid jobs in database
        valid_job = jobs_repo.get_job_by_url("https://linkedin.com/jobs/view/valid")
        assert valid_job is not None
        assert valid_job.posted_date == date(2025, 1, 15)

        invalid_job = jobs_repo.get_job_by_url("https://linkedin.com/jobs/view/invalid")
        assert invalid_job is not None
        assert invalid_job.posted_date is None  # Invalid date becomes None

    def test_database_constraint_handling(self, linkedin_poller, jobs_repo, mock_mcp_client):
        """Test handling of database constraint violations."""
        # Manually insert a job first
        existing_job = Job(
            company_name="Existing Company",
            job_title="Existing Job",
            job_url="https://linkedin.com/jobs/view/existing",
            platform_source="linkedin",
        )
        jobs_repo.insert_job(existing_job)

        # Mock MCP response with same URL
        mock_jobs = [
            {
                "title": "Duplicate Job",
                "company": "Different Company",
                "job_url": "https://linkedin.com/jobs/view/existing",  # Same URL
                "posted_date": "2025-01-15",
            }
        ]
        mock_mcp_client.call_tool.return_value = {"jobs": mock_jobs, "total_results": 1}

        # Run poll cycle
        metrics = linkedin_poller.run_once()

        # Job should be detected as duplicate
        assert metrics["duplicates_skipped"] == 1
        assert metrics["jobs_inserted"] == 0

    def test_configuration_loading_and_usage(self, linkedin_poller, mock_mcp_client):
        """Test that configuration is properly loaded and used."""
        mock_mcp_client.call_tool.return_value = {"jobs": [], "total_results": 0}

        # Run poll cycle
        linkedin_poller.run_once()

        # Verify MCP was called with config parameters
        mock_mcp_client.call_tool.assert_called_once()
        call_args = mock_mcp_client.call_tool.call_args
        params = call_args[1]["params"]

        # Check that keywords from config were used
        assert "Data Engineer" in params["query"]
        assert params["location"] == "Australia"
        assert params["job_type"] == "contract"

    def test_metrics_accuracy(self, linkedin_poller, jobs_repo, mock_mcp_client):
        """Test that metrics accurately reflect processing results."""
        # Insert one existing job
        existing_job = Job(
            company_name="Existing",
            job_title="Job",
            job_url="https://linkedin.com/jobs/view/existing",
            platform_source="linkedin",
        )
        jobs_repo.insert_job(existing_job)

        # Mock MCP response with 3 jobs (1 duplicate, 2 new)
        mock_jobs = [
            {
                "title": "Job 1",
                "company": "Co1",
                "job_url": "https://linkedin.com/jobs/view/existing",
                "posted_date": "2025-01-15",
            },
            {
                "title": "Job 2",
                "company": "Co2",
                "job_url": "https://linkedin.com/jobs/view/new1",
                "posted_date": "2025-01-15",
            },
            {
                "title": "Job 3",
                "company": "Co3",
                "job_url": "https://linkedin.com/jobs/view/new2",
                "posted_date": "2025-01-15",
            },
        ]
        mock_mcp_client.call_tool.return_value = {"jobs": mock_jobs, "total_results": 3}

        # Run poll cycle
        metrics = linkedin_poller.run_once()

        # Verify metrics
        assert metrics["jobs_found"] == 3
        assert metrics["jobs_inserted"] == 2
        assert metrics["duplicates_skipped"] == 1
        assert metrics["errors"] == 0

        # Verify total jobs in database
        all_jobs = jobs_repo.list_jobs(limit=10)
        assert len(all_jobs) == 3  # 1 existing + 2 new


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
