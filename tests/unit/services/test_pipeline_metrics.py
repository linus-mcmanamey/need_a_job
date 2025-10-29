"""
Unit tests for PipelineMetricsService.

Tests pipeline metrics calculations and real-time agent flow tracking.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.services.pipeline_metrics import PipelineMetricsService


@pytest.fixture
def mock_db():
    """Provide mock database connection."""
    return MagicMock()


@pytest.fixture
def pipeline_service(mock_db):
    """Provide PipelineMetricsService instance."""
    return PipelineMetricsService(mock_db)


class TestActiveJobsInPipeline:
    """Test active jobs in pipeline retrieval."""

    def test_get_active_jobs_in_pipeline(self, pipeline_service, mock_db):
        """Test getting active jobs currently in pipeline."""
        now = datetime(2025, 10, 29, 15, 0, 0)
        mock_db.execute.return_value.fetchall.return_value = [
            ("job-1", "Senior Data Engineer", "Tech Corp", "cv_tailor", "matched", now - timedelta(minutes=5), 300),
            ("job-2", "ML Engineer", "AI Startup", "job_matcher", "discovered", now - timedelta(minutes=2), 120),
        ]

        jobs = pipeline_service.get_active_jobs_in_pipeline()

        assert len(jobs) == 2
        assert jobs[0]["job_id"] == "job-1"
        assert jobs[0]["job_title"] == "Senior Data Engineer"
        assert jobs[0]["current_stage"] == "cv_tailor"
        assert jobs[0]["time_in_stage"] == "5m 0s"

    def test_get_active_jobs_excludes_completed(self, pipeline_service, mock_db):
        """Test that completed/rejected/duplicate jobs are excluded."""
        mock_db.execute.return_value.fetchall.return_value = []

        jobs = pipeline_service.get_active_jobs_in_pipeline()

        # Verify SQL filters out completed, rejected, duplicate
        sql = mock_db.execute.call_args[0][0]
        assert "NOT IN" in sql
        assert "completed" in sql or "rejected" in sql
        assert len(jobs) == 0

    def test_get_active_jobs_empty(self, pipeline_service, mock_db):
        """Test when no active jobs in pipeline."""
        mock_db.execute.return_value.fetchall.return_value = []

        jobs = pipeline_service.get_active_jobs_in_pipeline()

        assert jobs == []


class TestAgentExecutionMetrics:
    """Test agent execution metrics calculation."""

    def test_get_agent_execution_metrics(self, pipeline_service, mock_db):
        """Test getting execution metrics for each agent."""
        mock_db.execute.return_value.fetchall.return_value = [("job_matcher", 2.5, 100, 95.0), ("cv_tailor", 15.3, 80, 87.5), ("orchestrator", 1.2, 90, 92.0)]

        metrics = pipeline_service.get_agent_execution_metrics()

        assert len(metrics) == 3
        assert metrics["job_matcher"]["avg_execution_time"] == 2.5
        assert metrics["job_matcher"]["total_executions"] == 100
        assert metrics["job_matcher"]["success_rate"] == 95.0

    def test_get_agent_execution_metrics_empty(self, pipeline_service, mock_db):
        """Test metrics when no agent executions yet."""
        mock_db.execute.return_value.fetchall.return_value = []

        metrics = pipeline_service.get_agent_execution_metrics()

        assert metrics == {}

    def test_get_agent_execution_metrics_handles_zero_division(self, pipeline_service, mock_db):
        """Test metrics handles zero executions gracefully."""
        mock_db.execute.return_value.fetchall.return_value = [("job_matcher", 0.0, 0, 0.0)]

        metrics = pipeline_service.get_agent_execution_metrics()

        assert metrics["job_matcher"]["total_executions"] == 0
        assert metrics["job_matcher"]["success_rate"] == 0.0


class TestStageBottlenecks:
    """Test pipeline stage bottleneck identification."""

    def test_get_stage_bottlenecks(self, pipeline_service, mock_db):
        """Test identifying stages with high job counts."""
        mock_db.execute.return_value.fetchall.return_value = [
            ("cv_tailor", 15, 450.0),  # 15 jobs waiting, avg 450 seconds
            ("job_matcher", 8, 120.0),
            ("orchestrator", 3, 60.0),
        ]

        bottlenecks = pipeline_service.get_stage_bottlenecks()

        assert len(bottlenecks) == 3
        assert bottlenecks[0]["stage"] == "cv_tailor"
        assert bottlenecks[0]["job_count"] == 15
        assert bottlenecks[0]["avg_wait_time"] == "7m 30s"

    def test_get_stage_bottlenecks_empty(self, pipeline_service, mock_db):
        """Test bottlenecks when pipeline is empty."""
        mock_db.execute.return_value.fetchall.return_value = []

        bottlenecks = pipeline_service.get_stage_bottlenecks()

        assert bottlenecks == []


class TestPipelineStageCounts:
    """Test pipeline stage job counts."""

    def test_get_pipeline_stage_counts(self, pipeline_service, mock_db):
        """Test getting count of jobs at each stage."""
        mock_db.execute.return_value.fetchall.return_value = [("discovered", 25), ("matched", 18), ("documents_generated", 12), ("sending", 5)]

        counts = pipeline_service.get_pipeline_stage_counts()

        assert counts == {"discovered": 25, "matched": 18, "documents_generated": 12, "sending": 5}

    def test_get_pipeline_stage_counts_empty(self, pipeline_service, mock_db):
        """Test stage counts when no jobs exist."""
        mock_db.execute.return_value.fetchall.return_value = []

        counts = pipeline_service.get_pipeline_stage_counts()

        assert counts == {}


class TestFormatTimeInStage:
    """Test time formatting helper function."""

    def test_format_time_seconds(self, pipeline_service):
        """Test formatting time in seconds."""
        assert pipeline_service.format_time_in_stage(45) == "45s"

    def test_format_time_minutes(self, pipeline_service):
        """Test formatting time in minutes."""
        assert pipeline_service.format_time_in_stage(150) == "2m 30s"

    def test_format_time_hours(self, pipeline_service):
        """Test formatting time in hours."""
        assert pipeline_service.format_time_in_stage(7380) == "2h 3m"

    def test_format_time_zero(self, pipeline_service):
        """Test formatting zero seconds."""
        assert pipeline_service.format_time_in_stage(0) == "0s"

    def test_format_time_large_value(self, pipeline_service):
        """Test formatting large time values."""
        # 25 hours = 90000 seconds
        assert pipeline_service.format_time_in_stage(90000) == "25h 0m"


class TestGetAllPipelineMetrics:
    """Test combined pipeline metrics retrieval."""

    def test_get_all_pipeline_metrics(self, pipeline_service):
        """Test getting all pipeline metrics at once."""
        from unittest.mock import patch

        with patch.object(pipeline_service, "get_active_jobs_in_pipeline", return_value=[{"job_id": "job-1"}]):
            with patch.object(pipeline_service, "get_agent_execution_metrics", return_value={"job_matcher": {}}):
                with patch.object(pipeline_service, "get_stage_bottlenecks", return_value=[]):
                    with patch.object(pipeline_service, "get_pipeline_stage_counts", return_value={"matched": 10}):
                        metrics = pipeline_service.get_all_pipeline_metrics()

        assert metrics["active_jobs"] == [{"job_id": "job-1"}]
        assert metrics["agent_metrics"] == {"job_matcher": {}}
        assert metrics["bottlenecks"] == []
        assert metrics["stage_counts"] == {"matched": 10}


class TestErrorHandling:
    """Test error handling in pipeline metrics."""

    def test_database_error_returns_fallback(self, pipeline_service, mock_db):
        """Test that database errors return fallback values."""
        mock_db.execute.side_effect = Exception("Database connection failed")

        jobs = pipeline_service.get_active_jobs_in_pipeline()

        assert jobs == []

    def test_empty_result_handled_gracefully(self, pipeline_service, mock_db):
        """Test that empty database results are handled gracefully."""
        mock_db.execute.return_value.fetchall.return_value = []

        metrics = pipeline_service.get_agent_execution_metrics()

        assert metrics == {}
