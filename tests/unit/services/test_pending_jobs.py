"""
Unit tests for PendingJobsService.

Tests pending jobs management, error handling, and action operations.
"""

import json
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.services.pending_jobs import PendingJobsService


@pytest.fixture
def mock_db():
    """Provide mock database connection."""
    return MagicMock()


@pytest.fixture
def pending_service(mock_db):
    """Provide PendingJobsService instance."""
    return PendingJobsService(mock_db)


class TestGetPendingJobs:
    """Test pending jobs retrieval."""

    def test_get_pending_jobs(self, pending_service, mock_db):
        """Test getting list of pending/failed jobs."""
        now = datetime(2025, 10, 29, 15, 0, 0)
        error_info = json.dumps({"error_type": "complex_form", "error_message": "Form too complex", "failed_stage": "form_handler"})

        mock_db.execute.return_value.fetchall.return_value = [
            ("job-1", "Senior Data Engineer", "Tech Corp", "seek", "failed", "form_handler", error_info, now),
            ("job-2", "ML Engineer", "AI Startup", "indeed", "pending", "cv_tailor", None, now),
        ]

        jobs = pending_service.get_pending_jobs()

        assert len(jobs) == 2
        assert jobs[0]["job_id"] == "job-1"
        assert jobs[0]["status"] == "failed"
        assert jobs[0]["error_type"] == "complex_form"
        assert jobs[0]["error_message"] == "Form too complex"

    def test_get_pending_jobs_with_limit(self, pending_service, mock_db):
        """Test pending jobs respects limit parameter."""
        mock_db.execute.return_value.fetchall.return_value = []

        pending_service.get_pending_jobs(limit=10)

        # Verify SQL contains LIMIT clause
        sql = mock_db.execute.call_args[0][0]
        assert "LIMIT" in sql

    def test_get_pending_jobs_empty(self, pending_service, mock_db):
        """Test when no pending jobs exist."""
        mock_db.execute.return_value.fetchall.return_value = []

        jobs = pending_service.get_pending_jobs()

        assert jobs == []

    def test_get_pending_jobs_malformed_json(self, pending_service, mock_db):
        """Test handling of malformed error_info JSON."""
        now = datetime(2025, 10, 29, 15, 0, 0)
        mock_db.execute.return_value.fetchall.return_value = [("job-1", "Data Engineer", "Corp", "seek", "failed", "qa_agent", "invalid json{", now)]

        jobs = pending_service.get_pending_jobs()

        assert len(jobs) == 1
        assert jobs[0]["error_type"] == "unknown"
        assert jobs[0]["error_message"] == "Error info unavailable"


class TestGetErrorSummary:
    """Test error summary aggregation."""

    def test_get_error_summary(self, pending_service, mock_db):
        """Test getting error summary by type."""
        mock_db.execute.return_value.fetchall.return_value = [("complex_form", 5), ("api_error", 3), ("validation_error", 2)]

        summary = pending_service.get_error_summary()

        assert summary == {"complex_form": 5, "api_error": 3, "validation_error": 2}

    def test_get_error_summary_empty(self, pending_service, mock_db):
        """Test error summary when no errors exist."""
        mock_db.execute.return_value.fetchall.return_value = []

        summary = pending_service.get_error_summary()

        assert summary == {}


class TestRetryJob:
    """Test job retry operation."""

    def test_retry_job_success(self, pending_service, mock_db):
        """Test successful job retry."""
        mock_db.execute.return_value.rowcount = 1

        result = pending_service.retry_job("job-1")

        assert result["success"] is True
        assert result["message"] == "Job queued for retry"
        assert result["job_id"] == "job-1"

        # Verify UPDATE was called
        sql = mock_db.execute.call_args[0][0]
        assert "UPDATE" in sql
        assert "error_info = NULL" in sql or "error_info IS NULL" in sql.replace("=", " IS ")

    def test_retry_job_not_found(self, pending_service, mock_db):
        """Test retrying non-existent job."""
        mock_db.execute.return_value.rowcount = 0

        result = pending_service.retry_job("nonexistent")

        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_retry_job_database_error(self, pending_service, mock_db):
        """Test retry when database error occurs."""
        mock_db.execute.side_effect = Exception("Database error")

        result = pending_service.retry_job("job-1")

        assert result["success"] is False
        assert "error" in result["message"].lower()


class TestSkipJob:
    """Test job skip operation."""

    def test_skip_job_success(self, pending_service, mock_db):
        """Test successful job skip."""
        mock_db.execute.return_value.rowcount = 1

        result = pending_service.skip_job("job-1", "Not interested")

        assert result["success"] is True
        assert result["message"] == "Job marked as rejected"
        assert result["job_id"] == "job-1"

        # Verify UPDATE was called with status='rejected'
        sql = mock_db.execute.call_args[0][0]
        assert "UPDATE" in sql
        assert "rejected" in sql

    def test_skip_job_not_found(self, pending_service, mock_db):
        """Test skipping non-existent job."""
        mock_db.execute.return_value.rowcount = 0

        result = pending_service.skip_job("nonexistent", "Reason")

        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_skip_job_database_error(self, pending_service, mock_db):
        """Test skip when database error occurs."""
        mock_db.execute.side_effect = Exception("Database error")

        result = pending_service.skip_job("job-1", "Reason")

        assert result["success"] is False
        assert "error" in result["message"].lower()


class TestMarkManualComplete:
    """Test manual completion operation."""

    def test_mark_manual_complete_success(self, pending_service, mock_db):
        """Test successful manual completion."""
        mock_db.execute.return_value.rowcount = 1

        result = pending_service.mark_manual_complete("job-1")

        assert result["success"] is True
        assert result["message"] == "Job marked as manually completed"
        assert result["job_id"] == "job-1"

        # Verify UPDATE was called with status='completed'
        sql = mock_db.execute.call_args[0][0]
        assert "UPDATE" in sql
        assert "completed" in sql

    def test_mark_manual_complete_not_found(self, pending_service, mock_db):
        """Test manual complete on non-existent job."""
        mock_db.execute.return_value.rowcount = 0

        result = pending_service.mark_manual_complete("nonexistent")

        assert result["success"] is False
        assert "not found" in result["message"].lower()

    def test_mark_manual_complete_database_error(self, pending_service, mock_db):
        """Test manual complete when database error occurs."""
        mock_db.execute.side_effect = Exception("Database error")

        result = pending_service.mark_manual_complete("job-1")

        assert result["success"] is False
        assert "error" in result["message"].lower()


class TestGetJobDetails:
    """Test job details retrieval."""

    def test_get_job_details(self, pending_service, mock_db):
        """Test getting detailed job information."""
        now = datetime(2025, 10, 29, 15, 0, 0)
        error_info = json.dumps({"error_type": "api_error", "error_message": "API timeout", "failed_stage": "orchestrator"})
        stage_outputs = json.dumps({"cv_tailor": {"status": "success"}, "qa_agent": {"status": "success"}})

        mock_db.execute.return_value.fetchone.return_value = ("job-1", "Senior Engineer", "Tech Corp", "seek", "https://seek.com/job-1", "failed", "orchestrator", error_info, stage_outputs, now)

        details = pending_service.get_job_details("job-1")

        assert details["job_id"] == "job-1"
        assert details["job_title"] == "Senior Engineer"
        assert details["status"] == "failed"
        assert details["error_type"] == "api_error"
        assert "cv_tailor" in details["completed_stages"]

    def test_get_job_details_not_found(self, pending_service, mock_db):
        """Test getting details for non-existent job."""
        mock_db.execute.return_value.fetchone.return_value = None

        details = pending_service.get_job_details("nonexistent")

        assert details == {}

    def test_get_job_details_null_fields(self, pending_service, mock_db):
        """Test job details with NULL JSON fields."""
        now = datetime(2025, 10, 29, 15, 0, 0)
        mock_db.execute.return_value.fetchone.return_value = (
            "job-1",
            "Engineer",
            "Corp",
            "indeed",
            "https://url",
            "pending",
            "cv_tailor",
            None,  # NULL error_info
            None,  # NULL stage_outputs
            now,
        )

        details = pending_service.get_job_details("job-1")

        assert details["job_id"] == "job-1"
        assert details["error_type"] == "unknown"
        assert details["completed_stages"] == []


class TestErrorHandling:
    """Test error handling in pending jobs service."""

    def test_database_error_returns_fallback(self, pending_service, mock_db):
        """Test that database errors return fallback values."""
        mock_db.execute.side_effect = Exception("Database connection failed")

        jobs = pending_service.get_pending_jobs()

        assert jobs == []

    def test_empty_result_handled_gracefully(self, pending_service, mock_db):
        """Test that empty database results are handled gracefully."""
        mock_db.execute.return_value.fetchall.return_value = []

        summary = pending_service.get_error_summary()

        assert summary == {}
