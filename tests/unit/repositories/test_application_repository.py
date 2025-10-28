"""
Unit tests for application repository.

Tests CRUD operations for the application_tracking table.
"""

import pytest

from app.models.application import Application
from app.models.job import Job
from app.repositories.application_repository import ApplicationRepository
from app.repositories.database import initialize_database
from app.repositories.jobs_repository import JobsRepository


@pytest.fixture
def repos():
    """Create repositories with initialized database."""
    initialize_database()
    return {"jobs": JobsRepository(), "applications": ApplicationRepository()}


@pytest.fixture
def sample_job(repos):
    """Create and insert a sample job for testing."""
    job = Job(company_name="Test Company", job_title="Data Engineer", job_url="https://linkedin.com/jobs/test", platform_source="linkedin")
    repos["jobs"].insert_job(job)
    return job


@pytest.fixture
def sample_application(sample_job):
    """Create a sample application for testing."""
    return Application(job_id=sample_job.job_id, status="discovered")


class TestApplicationRepositoryInsert:
    """Test application insertion operations."""

    def test_insert_application_creates_record(self, repos, sample_application):
        """Test that insert_application creates a new record."""
        app_id = repos["applications"].insert_application(sample_application)
        assert app_id is not None
        assert isinstance(app_id, str)
        assert len(app_id) == 36  # UUID length

    def test_insert_application_returns_correct_id(self, repos, sample_application):
        """Test that insert_application returns the application's ID."""
        app_id = repos["applications"].insert_application(sample_application)
        assert app_id == sample_application.application_id

    def test_insert_application_with_invalid_job_id_succeeds(self, repos):
        """Test that application can be inserted without foreign key constraint.

        Note: Foreign key constraint was removed due to DuckDB limitations.
        Referential integrity is maintained at the application layer.
        """
        invalid_app = Application(
            job_id="00000000-0000-0000-0000-000000000000",  # Non-existent job
            status="discovered",
        )

        # Should succeed without foreign key constraint
        app_id = repos["applications"].insert_application(invalid_app)
        assert app_id is not None


class TestApplicationRepositoryGet:
    """Test application retrieval operations."""

    def test_get_application_by_id_returns_application(self, repos, sample_application):
        """Test retrieving application by ID."""
        app_id = repos["applications"].insert_application(sample_application)
        retrieved_app = repos["applications"].get_application_by_id(app_id)

        assert retrieved_app is not None
        assert retrieved_app.application_id == app_id
        assert retrieved_app.job_id == sample_application.job_id
        assert retrieved_app.status == sample_application.status

    def test_get_application_by_id_returns_none_for_nonexistent(self, repos):
        """Test that get_application_by_id returns None for non-existent ID."""
        result = repos["applications"].get_application_by_id("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_get_application_by_job_id_returns_application(self, repos, sample_application):
        """Test retrieving application by job ID."""
        repos["applications"].insert_application(sample_application)
        retrieved_app = repos["applications"].get_application_by_job_id(sample_application.job_id)

        assert retrieved_app is not None
        assert retrieved_app.job_id == sample_application.job_id

    def test_get_application_by_job_id_returns_none_for_nonexistent(self, repos):
        """Test that get_application_by_job_id returns None for non-existent job ID."""
        result = repos["applications"].get_application_by_job_id("00000000-0000-0000-0000-000000000000")
        assert result is None


class TestApplicationRepositoryUpdate:
    """Test application update operations."""

    def test_update_application_status_changes_status(self, repos, sample_application):
        """Test that update_application_status changes the status."""
        app_id = repos["applications"].insert_application(sample_application)

        repos["applications"].update_application_status(app_id, "matched")

        updated_app = repos["applications"].get_application_by_id(app_id)
        assert updated_app.status == "matched"

    def test_update_application_stage_updates_stage_data(self, repos, sample_application):
        """Test that update_application_stage updates stage information."""
        app_id = repos["applications"].insert_application(sample_application)

        stage_output = {"match_score": 0.85, "match_reasons": ["Python", "Cloud"]}
        repos["applications"].update_application_stage(app_id, "job_matcher_agent", stage_output)

        updated_app = repos["applications"].get_application_by_id(app_id)
        assert updated_app.current_stage == "job_matcher_agent"
        assert "job_matcher_agent" in updated_app.completed_stages
        assert updated_app.stage_outputs["job_matcher_agent"] == stage_output

    def test_update_application_error_sets_error_info(self, repos, sample_application):
        """Test that update_application_error sets error information."""
        app_id = repos["applications"].insert_application(sample_application)

        repos["applications"].update_application_error(app_id, "cv_tailor_agent", "APIError", "Claude API timeout")

        updated_app = repos["applications"].get_application_by_id(app_id)
        assert updated_app.status == "failed"
        assert updated_app.error_info is not None
        assert updated_app.error_info["stage"] == "cv_tailor_agent"
        assert updated_app.error_info["error_type"] == "APIError"


class TestApplicationRepositoryList:
    """Test application listing operations."""

    def test_list_applications_returns_all(self, repos, sample_job):
        """Test listing all applications."""
        app1 = Application(job_id=sample_job.job_id, status="discovered")
        app2 = Application(job_id=sample_job.job_id, status="matched")

        repos["applications"].insert_application(app1)
        repos["applications"].insert_application(app2)

        applications = repos["applications"].list_applications()
        assert len(applications) == 2

    def test_list_applications_with_status_filter(self, repos, sample_job):
        """Test filtering applications by status."""
        app1 = Application(job_id=sample_job.job_id, status="discovered")
        app2 = Application(job_id=sample_job.job_id, status="matched")
        app3 = Application(job_id=sample_job.job_id, status="matched")

        repos["applications"].insert_application(app1)
        repos["applications"].insert_application(app2)
        repos["applications"].insert_application(app3)

        matched_apps = repos["applications"].list_applications(filters={"status": "matched"})
        assert len(matched_apps) == 2
        assert all(app.status == "matched" for app in matched_apps)

    def test_list_applications_with_pagination(self, repos, sample_job):
        """Test pagination for applications."""
        for _i in range(5):
            app = Application(job_id=sample_job.job_id, status="discovered")
            repos["applications"].insert_application(app)

        first_page = repos["applications"].list_applications(limit=2, offset=0)
        second_page = repos["applications"].list_applications(limit=2, offset=2)

        assert len(first_page) == 2
        assert len(second_page) == 2
        assert first_page[0].application_id != second_page[0].application_id


class TestApplicationCascadeDelete:
    """Test cascade delete behavior."""

    def test_deleting_job_deletes_applications(self, repos, sample_job):
        """Test that deleting a job deletes associated applications."""
        app = Application(job_id=sample_job.job_id, status="discovered")
        app_id = repos["applications"].insert_application(app)

        # Delete the job
        repos["jobs"].delete_job(sample_job.job_id)

        # Application should be deleted due to CASCADE
        deleted_app = repos["applications"].get_application_by_id(app_id)
        assert deleted_app is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
