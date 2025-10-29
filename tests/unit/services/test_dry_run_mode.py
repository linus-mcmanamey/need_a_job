"""
Unit tests for DryRunModeService.

Tests dry-run mode toggle, dry-run results view, send now action,
and dry-run analytics metrics.
"""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.services.dry_run_mode import DryRunModeService


@pytest.fixture
def mock_db():
    """Create a mock database connection."""
    db = MagicMock()
    db.commit = MagicMock()
    return db


@pytest.fixture
def dry_run_service(mock_db):
    """Create DryRunModeService instance with mock database."""
    service = DryRunModeService(mock_db)
    # Reset mock to ignore initialization calls
    mock_db.reset_mock()
    return service


class TestGetDryRunModeEnabled:
    """Test get_dry_run_mode_enabled() method."""

    def test_get_dry_run_mode_enabled_true(self, dry_run_service, mock_db):
        """Test getting dry-run mode when enabled."""
        mock_db.execute.return_value.fetchone.return_value = ("true",)

        enabled = dry_run_service.get_dry_run_mode_enabled()

        assert enabled is True
        mock_db.execute.assert_called_once()
        assert "system_config" in mock_db.execute.call_args[0][0]
        assert "dry_run_mode_enabled" in mock_db.execute.call_args[0][0]

    def test_get_dry_run_mode_enabled_false(self, dry_run_service, mock_db):
        """Test getting dry-run mode when disabled."""
        mock_db.execute.return_value.fetchone.return_value = ("false",)

        enabled = dry_run_service.get_dry_run_mode_enabled()

        assert enabled is False

    def test_get_dry_run_mode_not_set(self, dry_run_service, mock_db):
        """Test getting dry-run mode when not set (default false)."""
        mock_db.execute.return_value.fetchone.return_value = None

        enabled = dry_run_service.get_dry_run_mode_enabled()

        assert enabled is False

    def test_get_dry_run_mode_database_error(self, dry_run_service, mock_db):
        """Test getting dry-run mode handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        enabled = dry_run_service.get_dry_run_mode_enabled()

        assert enabled is False


class TestSetDryRunMode:
    """Test set_dry_run_mode() method."""

    def test_set_dry_run_mode_enable(self, dry_run_service, mock_db):
        """Test enabling dry-run mode."""
        result = dry_run_service.set_dry_run_mode(True)

        assert result is True
        mock_db.execute.assert_called_once()
        assert "INSERT INTO system_config" in mock_db.execute.call_args[0][0]
        assert "ON CONFLICT" in mock_db.execute.call_args[0][0]
        mock_db.commit.assert_called_once()

    def test_set_dry_run_mode_disable(self, dry_run_service, mock_db):
        """Test disabling dry-run mode."""
        result = dry_run_service.set_dry_run_mode(False)

        assert result is True
        mock_db.commit.assert_called_once()

    def test_set_dry_run_mode_database_error(self, dry_run_service, mock_db):
        """Test set_dry_run_mode handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        result = dry_run_service.set_dry_run_mode(True)

        assert result is False
        mock_db.commit.assert_not_called()


class TestGetDryRunResults:
    """Test get_dry_run_results() method."""

    def test_get_dry_run_results(self, dry_run_service, mock_db):
        """Test retrieving dry-run results."""
        created = datetime(2025, 10, 30, 10, 0, 0)
        updated = datetime(2025, 10, 30, 11, 0, 0)

        mock_db.execute.return_value.fetchall.return_value = [
            ("job-1", "Senior Engineer", "TechCorp", "seek", 0.92, "/path/to/cv1.pdf", "/path/to/cl1.pdf", created, updated),
            ("job-2", "Data Analyst", "DataCo", "linkedin", 0.85, "/path/to/cv2.pdf", "/path/to/cl2.pdf", created, updated),
        ]

        jobs = dry_run_service.get_dry_run_results()

        assert len(jobs) == 2
        assert jobs[0]["job_id"] == "job-1"
        assert jobs[0]["job_title"] == "Senior Engineer"
        assert jobs[0]["company_name"] == "TechCorp"
        assert jobs[0]["platform"] == "seek"
        assert jobs[0]["match_score"] == 0.92
        assert jobs[0]["cv_path"] == "/path/to/cv1.pdf"
        assert jobs[0]["cl_path"] == "/path/to/cl1.pdf"

    def test_get_dry_run_results_with_limit(self, dry_run_service, mock_db):
        """Test dry-run results respects limit parameter."""
        mock_db.execute.return_value.fetchall.return_value = []

        dry_run_service.get_dry_run_results(limit=10)

        assert mock_db.execute.call_args[0][1] == (10,)

    def test_get_dry_run_results_empty(self, dry_run_service, mock_db):
        """Test dry-run results returns empty list when no jobs."""
        mock_db.execute.return_value.fetchall.return_value = []

        jobs = dry_run_service.get_dry_run_results()

        assert jobs == []

    def test_get_dry_run_results_database_error(self, dry_run_service, mock_db):
        """Test dry-run results handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        jobs = dry_run_service.get_dry_run_results()

        assert jobs == []


class TestGetDryRunAnalytics:
    """Test get_dry_run_analytics() method."""

    def test_get_dry_run_analytics(self, dry_run_service, mock_db):
        """Test retrieving dry-run analytics metrics."""
        newest_date = datetime(2025, 10, 30, 10, 0, 0)

        # Mock dry-run mode enabled call and analytics
        mock_db.execute.return_value.fetchone.side_effect = [
            ("true",),  # dry_run_mode_enabled
            (5, 0.87, newest_date),  # analytics metrics
        ]

        analytics = dry_run_service.get_dry_run_analytics()

        assert analytics["dry_run_count"] == 5
        assert analytics["avg_match_score"] == 0.87
        assert analytics["newest_job_hours"] >= 0
        assert analytics["dry_run_mode_enabled"] is True

    def test_get_dry_run_analytics_no_jobs(self, dry_run_service, mock_db):
        """Test dry-run analytics when no dry-run jobs."""
        mock_db.execute.return_value.fetchone.side_effect = [
            ("false",),  # dry_run_mode_enabled
            (0, None, None),  # analytics metrics
        ]

        analytics = dry_run_service.get_dry_run_analytics()

        assert analytics["dry_run_count"] == 0
        assert analytics["avg_match_score"] == 0.0
        assert analytics["newest_job_hours"] == 0
        assert analytics["dry_run_mode_enabled"] is False

    def test_get_dry_run_analytics_database_error(self, dry_run_service, mock_db):
        """Test dry-run analytics handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        analytics = dry_run_service.get_dry_run_analytics()

        assert analytics["dry_run_count"] == 0
        assert analytics["avg_match_score"] == 0.0
        assert analytics["newest_job_hours"] == 0
        assert analytics["dry_run_mode_enabled"] is False


class TestSendNow:
    """Test send_now() method."""

    def test_send_now_success(self, dry_run_service, mock_db):
        """Test sending dry-run job to live successfully."""
        mock_db.execute.return_value.rowcount = 1

        result = dry_run_service.send_now("job-123")

        assert result["success"] is True
        assert result["message"] == "Job moved to ready_to_send"
        assert result["job_id"] == "job-123"
        mock_db.execute.assert_called_once()
        assert "UPDATE application_tracking" in mock_db.execute.call_args[0][0]
        assert "status = 'ready_to_send'" in mock_db.execute.call_args[0][0]
        assert "status = 'dry_run_complete'" in mock_db.execute.call_args[0][0]
        mock_db.commit.assert_called_once()

    def test_send_now_not_found(self, dry_run_service, mock_db):
        """Test sending a job that doesn't exist or isn't dry-run."""
        mock_db.execute.return_value.rowcount = 0

        result = dry_run_service.send_now("job-999")

        assert result["success"] is False
        assert result["message"] == "Job not found or not in dry-run state"
        assert result["job_id"] == "job-999"
        mock_db.commit.assert_called_once()

    def test_send_now_database_error(self, dry_run_service, mock_db):
        """Test send_now handles database errors."""
        mock_db.execute.side_effect = Exception("Database error")

        result = dry_run_service.send_now("job-123")

        assert result["success"] is False
        assert "Error" in result["message"]
        assert result["job_id"] == "job-123"
        mock_db.commit.assert_not_called()
