"""
Unit tests for jobs repository.

Tests CRUD operations for the jobs table.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.models.job import Job
from app.repositories.database import initialize_database
from app.repositories.jobs_repository import JobsRepository


@pytest.fixture
def jobs_repo():
    """Create jobs repository with initialized database."""
    initialize_database()
    return JobsRepository()


@pytest.fixture
def sample_job():
    """Create a sample job for testing."""
    return Job(
        company_name="Test Company",
        job_title="Senior Data Engineer",
        job_url="https://linkedin.com/jobs/test-job-123",
        platform_source="linkedin",
        salary_aud_per_day=Decimal("1200.00"),
        location="Remote - Australia",
        posted_date=date(2025, 1, 15),
        job_description="Exciting opportunity for a data engineer...",
        requirements="Python, SQL, Cloud",
        responsibilities="Build data pipelines",
    )


class TestJobsRepositoryInsert:
    """Test job insertion operations."""

    def test_insert_job_creates_record(self, jobs_repo, sample_job):
        """Test that insert_job creates a new job record."""
        job_id = jobs_repo.insert_job(sample_job)
        assert job_id is not None
        assert isinstance(job_id, str)
        assert len(job_id) == 36  # UUID length with hyphens

    def test_insert_job_returns_correct_id(self, jobs_repo, sample_job):
        """Test that insert_job returns the job's ID."""
        job_id = jobs_repo.insert_job(sample_job)
        assert job_id == sample_job.job_id

    def test_insert_duplicate_url_raises_error(self, jobs_repo, sample_job):
        """Test that inserting duplicate job_url raises an error."""
        jobs_repo.insert_job(sample_job)

        duplicate_job = Job(
            company_name="Another Company",
            job_title="Different Title",
            job_url=sample_job.job_url,  # Same URL
            platform_source="linkedin",
        )

        with pytest.raises(Exception):  # DuckDB Constraint error
            jobs_repo.insert_job(duplicate_job)


class TestJobsRepositoryGet:
    """Test job retrieval operations."""

    def test_get_job_by_id_returns_job(self, jobs_repo, sample_job):
        """Test retrieving job by ID."""
        job_id = jobs_repo.insert_job(sample_job)
        retrieved_job = jobs_repo.get_job_by_id(job_id)

        assert retrieved_job is not None
        assert retrieved_job.job_id == job_id
        assert retrieved_job.company_name == sample_job.company_name
        assert retrieved_job.job_title == sample_job.job_title

    def test_get_job_by_id_returns_none_for_nonexistent(self, jobs_repo):
        """Test that get_job_by_id returns None for non-existent ID."""
        result = jobs_repo.get_job_by_id("00000000-0000-0000-0000-000000000000")
        assert result is None

    def test_get_job_by_url_returns_job(self, jobs_repo, sample_job):
        """Test retrieving job by URL."""
        jobs_repo.insert_job(sample_job)
        retrieved_job = jobs_repo.get_job_by_url(sample_job.job_url)

        assert retrieved_job is not None
        assert retrieved_job.job_url == sample_job.job_url
        assert retrieved_job.company_name == sample_job.company_name

    def test_get_job_by_url_returns_none_for_nonexistent(self, jobs_repo):
        """Test that get_job_by_url returns None for non-existent URL."""
        result = jobs_repo.get_job_by_url("https://nonexistent.com/job")
        assert result is None


class TestJobsRepositoryUpdate:
    """Test job update operations."""

    def test_update_job_modifies_fields(self, jobs_repo, sample_job):
        """Test that update_job modifies job fields."""
        job_id = jobs_repo.insert_job(sample_job)

        updates = {"salary_aud_per_day": 1500.00, "location": "Hybrid - Melbourne"}
        jobs_repo.update_job(job_id, updates)

        updated_job = jobs_repo.get_job_by_id(job_id)
        assert updated_job.salary_aud_per_day == Decimal("1500.00")
        assert updated_job.location == "Hybrid - Melbourne"
        assert updated_job.company_name == sample_job.company_name  # Unchanged

    def test_update_nonexistent_job_does_nothing(self, jobs_repo):
        """Test that updating non-existent job doesn't raise error."""
        # Should not raise error, just do nothing
        jobs_repo.update_job("00000000-0000-0000-0000-000000000000", {"location": "Test"})


class TestJobsRepositoryDelete:
    """Test job deletion operations."""

    def test_delete_job_removes_record(self, jobs_repo, sample_job):
        """Test that delete_job removes the job."""
        job_id = jobs_repo.insert_job(sample_job)
        jobs_repo.delete_job(job_id)

        deleted_job = jobs_repo.get_job_by_id(job_id)
        assert deleted_job is None

    def test_delete_nonexistent_job_does_nothing(self, jobs_repo):
        """Test that deleting non-existent job doesn't raise error."""
        # Should not raise error
        jobs_repo.delete_job("00000000-0000-0000-0000-000000000000")


class TestJobsRepositoryList:
    """Test job listing operations."""

    def test_list_jobs_returns_all_jobs(self, jobs_repo, sample_job):
        """Test listing all jobs."""
        job1 = sample_job
        job2 = Job(company_name="Company 2", job_title="Data Analyst", job_url="https://linkedin.com/jobs/test-job-456", platform_source="linkedin")

        jobs_repo.insert_job(job1)
        jobs_repo.insert_job(job2)

        jobs = jobs_repo.list_jobs()
        assert len(jobs) == 2
        assert any(j.job_url == job1.job_url for j in jobs)
        assert any(j.job_url == job2.job_url for j in jobs)

    def test_list_jobs_with_limit(self, jobs_repo, sample_job):
        """Test listing jobs with limit."""
        for i in range(5):
            job = Job(company_name=f"Company {i}", job_title=f"Engineer {i}", job_url=f"https://linkedin.com/jobs/test-{i}", platform_source="linkedin")
            jobs_repo.insert_job(job)

        jobs = jobs_repo.list_jobs(limit=3)
        assert len(jobs) == 3

    def test_list_jobs_with_offset(self, jobs_repo, sample_job):
        """Test listing jobs with offset for pagination."""
        for i in range(5):
            job = Job(company_name=f"Company {i}", job_title=f"Engineer {i}", job_url=f"https://linkedin.com/jobs/test-{i}", platform_source="linkedin")
            jobs_repo.insert_job(job)

        first_page = jobs_repo.list_jobs(limit=2, offset=0)
        second_page = jobs_repo.list_jobs(limit=2, offset=2)

        assert len(first_page) == 2
        assert len(second_page) == 2
        # Ensure different jobs returned
        assert first_page[0].job_id != second_page[0].job_id

    def test_list_jobs_with_platform_filter(self, jobs_repo):
        """Test filtering jobs by platform."""
        linkedin_job = Job(company_name="LinkedIn Company", job_title="Engineer", job_url="https://linkedin.com/jobs/test-1", platform_source="linkedin")
        seek_job = Job(company_name="SEEK Company", job_title="Engineer", job_url="https://seek.com/jobs/test-2", platform_source="seek")

        jobs_repo.insert_job(linkedin_job)
        jobs_repo.insert_job(seek_job)

        linkedin_jobs = jobs_repo.list_jobs(filters={"platform_source": "linkedin"})
        assert len(linkedin_jobs) == 1
        assert linkedin_jobs[0].platform_source == "linkedin"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
