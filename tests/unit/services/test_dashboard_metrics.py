"""
Unit tests for DashboardMetricsService.

Tests dashboard metrics calculations and aggregations.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.dashboard_metrics import DashboardMetricsService


@pytest.fixture
def mock_db():
    """Provide mock database connection."""
    return MagicMock()


@pytest.fixture
def metrics_service(mock_db):
    """Provide DashboardMetricsService instance."""
    return DashboardMetricsService(mock_db)


class TestJobsDiscoveredToday:
    """Test jobs discovered today metric."""

    def test_get_jobs_discovered_today(self, metrics_service, mock_db):
        """Test getting count of jobs discovered today."""
        mock_db.execute.return_value.fetchone.return_value = (42,)

        count = metrics_service.get_jobs_discovered_today()

        assert count == 42
        mock_db.execute.assert_called_once()
        # Verify SQL contains today's date filter
        sql = mock_db.execute.call_args[0][0]
        assert "CURRENT_DATE" in sql or "DATE(created_at)" in sql

    def test_get_jobs_discovered_today_none(self, metrics_service, mock_db):
        """Test when no jobs discovered today."""
        mock_db.execute.return_value.fetchone.return_value = (0,)

        count = metrics_service.get_jobs_discovered_today()

        assert count == 0


class TestApplicationsSent:
    """Test applications sent metric."""

    def test_get_applications_sent_all_time(self, metrics_service, mock_db):
        """Test getting all-time applications sent."""
        mock_db.execute.return_value.fetchone.return_value = (123,)

        count = metrics_service.get_applications_sent(period="all")

        assert count == 123

    def test_get_applications_sent_today(self, metrics_service, mock_db):
        """Test getting applications sent today."""
        mock_db.execute.return_value.fetchone.return_value = (15,)

        count = metrics_service.get_applications_sent(period="today")

        assert count == 15


class TestPendingCount:
    """Test pending jobs count."""

    def test_get_pending_count(self, metrics_service, mock_db):
        """Test getting count of pending jobs."""
        mock_db.execute.return_value.fetchone.return_value = (7,)

        count = metrics_service.get_pending_count()

        assert count == 7
        # Verify SQL filters for pending/failed statuses
        sql = mock_db.execute.call_args[0][0]
        assert "pending" in sql.lower() or "failed" in sql.lower()


class TestSuccessRate:
    """Test success rate calculation."""

    def test_get_success_rate(self, metrics_service, mock_db):
        """Test success rate calculation."""
        # Mock: 80 completed out of 100 total
        mock_db.execute.return_value.fetchone.side_effect = [(100,), (80,)]

        rate = metrics_service.get_success_rate()

        assert rate == 80.0

    def test_get_success_rate_no_jobs(self, metrics_service, mock_db):
        """Test success rate when no jobs exist."""
        mock_db.execute.return_value.fetchone.return_value = (0,)

        rate = metrics_service.get_success_rate()

        assert rate == 0.0

    def test_get_success_rate_zero_completed(self, metrics_service, mock_db):
        """Test success rate when no completed applications."""
        mock_db.execute.return_value.fetchone.side_effect = [(50,), (0,)]

        rate = metrics_service.get_success_rate()

        assert rate == 0.0


class TestStatusBreakdown:
    """Test status breakdown aggregation."""

    def test_get_status_breakdown(self, metrics_service, mock_db):
        """Test getting status breakdown."""
        mock_db.execute.return_value.fetchall.return_value = [("discovered", 25), ("matched", 15), ("completed", 50), ("pending", 10)]

        breakdown = metrics_service.get_status_breakdown()

        assert breakdown == {"discovered": 25, "matched": 15, "completed": 50, "pending": 10}

    def test_get_status_breakdown_empty(self, metrics_service, mock_db):
        """Test status breakdown when no data."""
        mock_db.execute.return_value.fetchall.return_value = []

        breakdown = metrics_service.get_status_breakdown()

        assert breakdown == {}


class TestRecentActivity:
    """Test recent activity feed."""

    def test_get_recent_activity(self, metrics_service, mock_db):
        """Test getting recent activity."""
        mock_db.execute.return_value.fetchall.return_value = [("job-1", "Senior Data Engineer", "Tech Corp", "completed", datetime(2025, 10, 29, 10, 0)), ("job-2", "ML Engineer", "AI Startup", "pending", datetime(2025, 10, 29, 9, 30))]

        activity = metrics_service.get_recent_activity(limit=10)

        assert len(activity) == 2
        assert activity[0]["job_id"] == "job-1"
        assert activity[0]["job_title"] == "Senior Data Engineer"
        assert activity[0]["company_name"] == "Tech Corp"
        assert activity[0]["status"] == "completed"

    def test_get_recent_activity_limit(self, metrics_service, mock_db):
        """Test recent activity respects limit."""
        mock_db.execute.return_value.fetchall.return_value = []

        metrics_service.get_recent_activity(limit=5)

        # Verify SQL contains LIMIT clause
        sql = mock_db.execute.call_args[0][0]
        assert "LIMIT" in sql

    def test_get_recent_activity_empty(self, metrics_service, mock_db):
        """Test recent activity when no data."""
        mock_db.execute.return_value.fetchall.return_value = []

        activity = metrics_service.get_recent_activity()

        assert activity == []


class TestGetAllMetrics:
    """Test combined metrics retrieval."""

    def test_get_all_metrics(self, metrics_service):
        """Test getting all metrics at once."""
        with patch.object(metrics_service, "get_jobs_discovered_today", return_value=10):
            with patch.object(metrics_service, "get_applications_sent", return_value=5):
                with patch.object(metrics_service, "get_pending_count", return_value=2):
                    with patch.object(metrics_service, "get_success_rate", return_value=85.5):
                        with patch.object(metrics_service, "get_status_breakdown", return_value={"completed": 50}):
                            with patch.object(metrics_service, "get_recent_activity", return_value=[]):
                                metrics = metrics_service.get_all_metrics()

        assert metrics["jobs_discovered_today"] == 10
        assert metrics["applications_sent_today"] == 5
        assert metrics["pending_count"] == 2
        assert metrics["success_rate"] == 85.5
        assert metrics["status_breakdown"] == {"completed": 50}
        assert metrics["recent_activity"] == []
