"""
Tests for application history API endpoint.

Tests the /api/history endpoint for filtering, sorting, and pagination.
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_applications(client):
    """Create sample application data for testing."""
    from app.models.job import Job
    from app.models.application import Application
    from app.repositories.jobs_repository import JobsRepository
    from app.repositories.application_repository import ApplicationRepository
    from app.repositories.database import get_connection

    # Clean database before test
    conn = get_connection()
    conn.execute("DELETE FROM application_tracking")
    conn.execute("DELETE FROM jobs")

    jobs_repo = JobsRepository()
    app_repo = ApplicationRepository()

    # Create test jobs
    jobs = [
        Job(company_name="Acme Corp", job_title="Senior Data Engineer", job_url="https://linkedin.com/jobs/1", platform_source="linkedin"),
        Job(company_name="Tech Solutions", job_title="Data Engineer", job_url="https://seek.com.au/jobs/2", platform_source="seek"),
        Job(company_name="Global Industries", job_title="Lead Data Engineer", job_url="https://indeed.com/jobs/3", platform_source="indeed"),
    ]

    for job in jobs:
        jobs_repo.insert_job(job)

    # Create test applications with different statuses and timestamps
    now = datetime.now()
    applications = [
        Application(job_id=jobs[0].job_id, status="completed", stage_outputs={"job_matcher": {"match_score": 85}}, submitted_timestamp=now - timedelta(days=5), cv_file_path="/path/to/cv1.docx", cl_file_path="/path/to/cl1.docx"),
        Application(job_id=jobs[1].job_id, status="completed", stage_outputs={"job_matcher": {"match_score": 92}}, submitted_timestamp=now - timedelta(days=2), cv_file_path="/path/to/cv2.docx", cl_file_path="/path/to/cl2.docx"),
        Application(job_id=jobs[2].job_id, status="rejected", stage_outputs={"job_matcher": {"match_score": 65}}, submitted_timestamp=now - timedelta(days=10), cv_file_path="/path/to/cv3.docx", cl_file_path="/path/to/cl3.docx"),
    ]

    for application in applications:
        app_repo.insert_application(application)

    return {"jobs": jobs, "applications": applications}


class TestHistoryEndpoint:
    """Test suite for /api/history endpoint."""

    def test_get_history_returns_200(self, client, sample_applications):
        """Test that GET /api/history returns 200 OK."""
        response = client.get("/api/history")
        assert response.status_code == 200

    def test_get_history_returns_application_list(self, client, sample_applications):
        """Test that history endpoint returns list of applications."""
        response = client.get("/api/history")
        data = response.json()

        assert "applications" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["applications"], list)
        assert data["total"] == 3

    def test_get_history_includes_job_details(self, client, sample_applications):
        """Test that each application includes job details."""
        response = client.get("/api/history")
        data = response.json()

        app = data["applications"][0]
        assert "application_id" in app
        assert "job_title" in app
        assert "company_name" in app
        assert "platform" in app
        assert "applied_date" in app
        assert "match_score" in app
        assert "status" in app
        assert "cv_file_path" in app
        assert "cl_file_path" in app
        assert "job_url" in app

    def test_get_history_filters_by_platform(self, client, sample_applications):
        """Test filtering by platform."""
        response = client.get("/api/history?platform=linkedin")
        data = response.json()

        assert data["total"] == 1
        assert data["applications"][0]["platform"] == "linkedin"

    def test_get_history_filters_by_multiple_platforms(self, client, sample_applications):
        """Test filtering by multiple platforms."""
        response = client.get("/api/history?platform=linkedin&platform=seek")
        data = response.json()

        assert data["total"] == 2
        platforms = [app["platform"] for app in data["applications"]]
        assert "linkedin" in platforms
        assert "seek" in platforms
        assert "indeed" not in platforms

    def test_get_history_filters_by_status(self, client, sample_applications):
        """Test filtering by status."""
        response = client.get("/api/history?status=completed")
        data = response.json()

        assert data["total"] == 2
        for application in data["applications"]:
            assert application["status"] == "completed"

    def test_get_history_filters_by_score_range(self, client, sample_applications):
        """Test filtering by match score range."""
        response = client.get("/api/history?min_score=80&max_score=95")
        data = response.json()

        assert data["total"] == 2
        for application in data["applications"]:
            assert 80 <= application["match_score"] <= 95

    def test_get_history_sorts_by_date_desc_default(self, client, sample_applications):
        """Test default sort is by applied_date descending."""
        response = client.get("/api/history")
        data = response.json()

        dates = [app["applied_date"] for app in data["applications"]]
        # Should be sorted most recent first
        assert dates == sorted(dates, reverse=True)

    def test_get_history_sorts_by_company_asc(self, client, sample_applications):
        """Test sorting by company name ascending."""
        response = client.get("/api/history?sort_by=company&sort_order=asc")
        data = response.json()

        companies = [app["company_name"] for app in data["applications"]]
        assert companies == sorted(companies)

    def test_get_history_pagination(self, client, sample_applications):
        """Test pagination works correctly."""
        response = client.get("/api/history?page=1&page_size=2")
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["applications"]) == 2
        assert data["total"] == 3

    def test_get_history_validates_page_size_max(self, client, sample_applications):
        """Test page_size is capped at 100."""
        response = client.get("/api/history?page_size=200")

        # Should either return 422 validation error or cap at 100
        if response.status_code == 200:
            data = response.json()
            assert data["page_size"] <= 100
        else:
            assert response.status_code == 422

    def test_get_history_invalid_sort_column(self, client, sample_applications):
        """Test invalid sort column returns 422."""
        response = client.get("/api/history?sort_by=invalid_column")
        assert response.status_code == 422

    def test_get_history_invalid_sort_order(self, client, sample_applications):
        """Test invalid sort order returns 422."""
        response = client.get("/api/history?sort_order=invalid")
        assert response.status_code == 422
