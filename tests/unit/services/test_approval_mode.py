"""
Unit tests for ApprovalModeService.

Tests approval mode toggle, pending approvals view, approve/reject actions,
and approval summary metrics.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.services.approval_mode import ApprovalModeService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    db = MagicMock()
    db.commit = MagicMock()
    return db


@pytest.fixture
def approval_service(mock_db):
    """Create ApprovalModeService instance with mock database."""
    service = ApprovalModeService(mock_db)
    # Reset mock to ignore initialization calls
    mock_db.reset_mock()
    return service


class TestGetApprovalModeEnabled:
    """Test get_approval_mode_enabled() method."""

    def test_get_approval_mode_enabled_true(self, approval_service, mock_db):
        """Test getting approval mode when enabled."""
        mock_db.execute.return_value.fetchone.return_value = ("true",)
        enabled = approval_service.get_approval_mode_enabled()

        assert enabled is True
        mock_db.execute.assert_called_once()
        assert "system_config" in mock_db.execute.call_args[0][0]
        assert "approval_mode_enabled" in mock_db.execute.call_args[0][0]

    def test_get_approval_mode_enabled_false(self, approval_service, mock_db):
        """Test getting approval mode when disabled."""
        mock_db.execute.return_value.fetchone.return_value = ("false",)

        enabled = approval_service.get_approval_mode_enabled()

        assert enabled is False

    def test_get_approval_mode_not_set(self, approval_service, mock_db):
        """Test getting approval mode when not set (default false)."""
        mock_db.execute.return_value.fetchone.return_value = None

        enabled = approval_service.get_approval_mode_enabled()

        assert enabled is False

    def test_get_approval_mode_database_error(self, approval_service, mock_db):
        """Test getting approval mode handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        enabled = approval_service.get_approval_mode_enabled()

        assert enabled is False


class TestSetApprovalMode:
    """Test set_approval_mode() method."""

    def test_set_approval_mode_enable(self, approval_service, mock_db):
        """Test enabling approval mode."""
        result = approval_service.set_approval_mode(True)

        assert result is True
        mock_db.execute.assert_called_once()
        assert "INSERT INTO system_config" in mock_db.execute.call_args[0][0]
        assert "ON CONFLICT" in mock_db.execute.call_args[0][0]
        mock_db.commit.assert_called_once()

    def test_set_approval_mode_disable(self, approval_service, mock_db):
        """Test disabling approval mode."""
        result = approval_service.set_approval_mode(False)

        assert result is True
        mock_db.commit.assert_called_once()

    def test_set_approval_mode_database_error(self, approval_service, mock_db):
        """Test set_approval_mode handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        result = approval_service.set_approval_mode(True)

        assert result is False
        mock_db.commit.assert_not_called()


class TestGetPendingApprovals:
    """Test get_pending_approvals() method."""

    def test_get_pending_approvals(self, approval_service, mock_db):
        """Test retrieving pending approvals."""
        created = datetime(2025, 10, 30, 10, 0, 0)
        updated = datetime(2025, 10, 30, 11, 0, 0)

        mock_db.execute.return_value.fetchall.return_value = [
            ("job-1", "Senior Engineer", "TechCorp", "seek", 0.92, "/path/to/cv1.pdf", "/path/to/cl1.pdf", created, updated),
            ("job-2", "Data Analyst", "DataCo", "linkedin", 0.85, "/path/to/cv2.pdf", "/path/to/cl2.pdf", created, updated),
        ]

        jobs = approval_service.get_pending_approvals()

        assert len(jobs) == 2
        assert jobs[0]["job_id"] == "job-1"
        assert jobs[0]["job_title"] == "Senior Engineer"
        assert jobs[0]["company_name"] == "TechCorp"
        assert jobs[0]["platform"] == "seek"
        assert jobs[0]["match_score"] == 0.92
        assert jobs[0]["cv_path"] == "/path/to/cv1.pdf"
        assert jobs[0]["cl_path"] == "/path/to/cl1.pdf"

    def test_get_pending_approvals_with_limit(self, approval_service, mock_db):
        """Test pending approvals respects limit parameter."""
        mock_db.execute.return_value.fetchall.return_value = []

        approval_service.get_pending_approvals(limit=10)

        assert mock_db.execute.call_args[0][1] == (10,)

    def test_get_pending_approvals_empty(self, approval_service, mock_db):
        """Test pending approvals returns empty list when no jobs."""
        mock_db.execute.return_value.fetchall.return_value = []

        jobs = approval_service.get_pending_approvals()

        assert jobs == []

    def test_get_pending_approvals_database_error(self, approval_service, mock_db):
        """Test pending approvals handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        jobs = approval_service.get_pending_approvals()

        assert jobs == []


class TestGetApprovalSummary:
    """Test get_approval_summary() method."""

    def test_get_approval_summary(self, approval_service, mock_db):
        """Test retrieving approval summary metrics."""
        oldest_date = datetime(2025, 10, 28, 10, 0, 0)

        # Mock approval mode enabled call
        mock_db.execute.return_value.fetchone.side_effect = [
            ("true",),  # approval_mode_enabled
            (5, 0.87, oldest_date),  # summary metrics
        ]

        summary = approval_service.get_approval_summary()

        assert summary["pending_count"] == 5
        assert summary["avg_match_score"] == 0.87
        # Days calculation depends on current time, should be >= 1
        assert summary["oldest_job_days"] >= 1
        assert summary["approval_mode_enabled"] is True

    def test_get_approval_summary_no_pending(self, approval_service, mock_db):
        """Test approval summary when no pending jobs."""
        mock_db.execute.return_value.fetchone.side_effect = [
            ("false",),  # approval_mode_enabled
            (0, None, None),  # summary metrics
        ]

        summary = approval_service.get_approval_summary()

        assert summary["pending_count"] == 0
        assert summary["avg_match_score"] == 0.0
        assert summary["oldest_job_days"] == 0
        assert summary["approval_mode_enabled"] is False

    def test_get_approval_summary_database_error(self, approval_service, mock_db):
        """Test approval summary handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        summary = approval_service.get_approval_summary()

        assert summary["pending_count"] == 0
        assert summary["avg_match_score"] == 0.0
        assert summary["oldest_job_days"] == 0
        assert summary["approval_mode_enabled"] is False


class TestApproveJob:
    """Test approve_job() method."""

    def test_approve_job_success(self, approval_service, mock_db):
        """Test approving a job successfully."""
        mock_db.execute.return_value.rowcount = 1

        result = approval_service.approve_job("job-123")

        assert result["success"] is True
        assert result["message"] == "Job approved and ready for submission"
        assert result["job_id"] == "job-123"
        mock_db.execute.assert_called_once()
        assert "UPDATE application_tracking" in mock_db.execute.call_args[0][0]
        assert "status = 'approved'" in mock_db.execute.call_args[0][0]
        mock_db.commit.assert_called_once()

    def test_approve_job_not_found(self, approval_service, mock_db):
        """Test approving a job that doesn't exist."""
        mock_db.execute.return_value.rowcount = 0

        result = approval_service.approve_job("job-999")

        assert result["success"] is False
        assert result["message"] == "Job not found"
        assert result["job_id"] == "job-999"
        mock_db.commit.assert_called_once()

    def test_approve_job_database_error(self, approval_service, mock_db):
        """Test approve_job handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        result = approval_service.approve_job("job-123")

        assert result["success"] is False
        assert "Error" in result["message"]
        assert result["job_id"] == "job-123"
        mock_db.commit.assert_not_called()


class TestRejectJob:
    """Test reject_job() method."""

    def test_reject_job_success(self, approval_service, mock_db):
        """Test rejecting a job successfully."""
        mock_db.execute.return_value.rowcount = 1

        result = approval_service.reject_job("job-123", "Not interested")

        assert result["success"] is True
        assert result["message"] == "Job rejected"
        assert result["job_id"] == "job-123"
        mock_db.execute.assert_called_once()
        assert "UPDATE application_tracking" in mock_db.execute.call_args[0][0]
        assert "status = 'rejected'" in mock_db.execute.call_args[0][0]
        # Verify JSON structure includes rejection reason
        assert mock_db.execute.call_args[0][1][0]  # rejection_info JSON
        mock_db.commit.assert_called_once()

    def test_reject_job_not_found(self, approval_service, mock_db):
        """Test rejecting a job that doesn't exist."""
        mock_db.execute.return_value.rowcount = 0

        result = approval_service.reject_job("job-999", "Not interested")

        assert result["success"] is False
        assert result["message"] == "Job not found"
        assert result["job_id"] == "job-999"
        mock_db.commit.assert_called_once()

    def test_reject_job_database_error(self, approval_service, mock_db):
        """Test reject_job handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        result = approval_service.reject_job("job-123", "Not interested")

        assert result["success"] is False
        assert "Error" in result["message"]
        assert result["job_id"] == "job-123"
        mock_db.commit.assert_not_called()
