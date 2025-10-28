"""Unit tests for RQ worker tasks."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest

from app.queue.worker_tasks import process_job


class TestProcessJob:
    """Test suite for process_job worker task."""

    def test_process_job_with_valid_job_id(self):
        """Test process_job executes successfully with valid job_id."""
        job_id = str(uuid4())

        with patch("app.queue.worker_tasks.get_redis_connection"):
            with patch("app.queue.worker_tasks.JobsRepository"):
                with patch("app.queue.worker_tasks.ApplicationRepository"):
                    with patch(
                        "app.queue.worker_tasks.JobProcessorService"
                    ) as mock_processor_class:
                        mock_processor = Mock()
                        mock_processor.process_job.return_value = {"status": "success"}
                        mock_processor_class.return_value = mock_processor

                        result = process_job(job_id)

                        assert result is not None
                        assert result["status"] == "success"
                        mock_processor.process_job.assert_called_once()

    def test_process_job_with_invalid_job_id(self):
        """Test process_job handles invalid job_id."""
        job_id = "not-a-uuid"

        with pytest.raises(ValueError):
            process_job(job_id)

    def test_process_job_updates_status_to_processing(self):
        """Test process_job updates status to 'processing' before execution."""
        job_id = str(uuid4())

        with patch("app.queue.worker_tasks.get_redis_connection"):
            with patch("app.queue.worker_tasks.JobsRepository"):
                with patch("app.queue.worker_tasks.ApplicationRepository") as mock_app_repo_class:
                    mock_app_repo = Mock()
                    mock_app_repo_class.return_value = mock_app_repo

                    with patch(
                        "app.queue.worker_tasks.JobProcessorService"
                    ) as mock_processor_class:
                        mock_processor = Mock()
                        mock_processor.process_job.return_value = {"status": "success"}
                        mock_processor_class.return_value = mock_processor

                        process_job(job_id)

                        # Should update status to 'processing'
                        assert mock_app_repo.update_status.called

    def test_process_job_handles_processor_exception(self):
        """Test process_job handles exceptions from processor."""
        job_id = str(uuid4())

        with patch("app.queue.worker_tasks.get_redis_connection"):
            with patch("app.queue.worker_tasks.JobsRepository"):
                with patch("app.queue.worker_tasks.ApplicationRepository") as mock_app_repo_class:
                    mock_app_repo = Mock()
                    mock_app_repo_class.return_value = mock_app_repo

                    with patch(
                        "app.queue.worker_tasks.JobProcessorService"
                    ) as mock_processor_class:
                        mock_processor = Mock()
                        mock_processor.process_job.side_effect = Exception("Processing failed")
                        mock_processor_class.return_value = mock_processor

                        with pytest.raises(Exception):
                            process_job(job_id)

                        # Should update status to 'failed'
                        assert mock_app_repo.update_status.called

    def test_process_job_is_idempotent(self):
        """Test process_job can be called multiple times safely."""
        job_id = str(uuid4())

        with patch("app.queue.worker_tasks.get_redis_connection"):
            with patch("app.queue.worker_tasks.JobsRepository"):
                with patch("app.queue.worker_tasks.ApplicationRepository"):
                    with patch(
                        "app.queue.worker_tasks.JobProcessorService"
                    ) as mock_processor_class:
                        mock_processor = Mock()
                        mock_processor.process_job.return_value = {"status": "success"}
                        mock_processor_class.return_value = mock_processor

                        # Call twice
                        result1 = process_job(job_id)
                        result2 = process_job(job_id)

                        # Both should succeed
                        assert result1["status"] == "success"
                        assert result2["status"] == "success"

    def test_process_job_returns_result_dict(self):
        """Test process_job returns result dictionary."""
        job_id = str(uuid4())

        with patch("app.queue.worker_tasks.get_redis_connection"):
            with patch("app.queue.worker_tasks.JobsRepository"):
                with patch("app.queue.worker_tasks.ApplicationRepository"):
                    with patch(
                        "app.queue.worker_tasks.JobProcessorService"
                    ) as mock_processor_class:
                        mock_processor = Mock()
                        mock_processor.process_job.return_value = {
                            "status": "success",
                            "job_id": job_id,
                            "stages_completed": ["matcher", "validator"],
                        }
                        mock_processor_class.return_value = mock_processor

                        result = process_job(job_id)

                        assert isinstance(result, dict)
                        assert "status" in result
                        assert "job_id" in result
                        assert result["job_id"] == job_id
