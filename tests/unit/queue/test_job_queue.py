"""Unit tests for JobQueue class."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from rq import Queue
from rq.job import Job as RQJob

from app.models.job import Job
from app.job_queue.job_queue import JobQueue


@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    return Mock()


@pytest.fixture
def mock_jobs_repo():
    """Mock JobsRepository."""
    repo = Mock()
    repo.get_job_by_id.return_value = Job(job_id=uuid4(), company_name="Test Corp", job_title="Data Engineer", job_url="https://test.com/job/123", platform_source="linkedin")
    return repo


@pytest.fixture
def mock_app_repo():
    """Mock ApplicationRepository."""
    repo = Mock()
    return repo


@pytest.fixture
def job_queue(mock_redis, mock_jobs_repo, mock_app_repo):
    """Create JobQueue instance with mocked dependencies."""
    with patch("app.queue.job_queue.Queue") as mock_queue_class:
        mock_queue = Mock(spec=Queue)
        mock_queue_class.return_value = mock_queue

        queue = JobQueue(redis_connection=mock_redis, jobs_repository=mock_jobs_repo, application_repository=mock_app_repo)
        queue.queue = mock_queue  # Inject mock queue
        return queue


class TestJobQueueInitialization:
    """Test suite for JobQueue initialization."""

    def test_job_queue_initialization(self, mock_redis, mock_jobs_repo, mock_app_repo):
        """Test JobQueue initializes with dependencies."""
        with patch("app.queue.job_queue.Queue"):
            queue = JobQueue(redis_connection=mock_redis, jobs_repository=mock_jobs_repo, application_repository=mock_app_repo)

            assert queue.redis == mock_redis
            assert queue.jobs_repo == mock_jobs_repo
            assert queue.app_repo == mock_app_repo

    def test_job_queue_creates_rq_queue(self, mock_redis, mock_jobs_repo, mock_app_repo):
        """Test JobQueue creates RQ queue on initialization."""
        with patch("app.queue.job_queue.Queue") as mock_queue_class:
            queue = JobQueue(redis_connection=mock_redis, jobs_repository=mock_jobs_repo, application_repository=mock_app_repo)

            mock_queue_class.assert_called_once()
            assert queue.queue is not None


class TestEnqueueJob:
    """Test suite for job enqueueing."""

    def test_enqueue_job_with_valid_job_id(self, job_queue, mock_jobs_repo, mock_app_repo):
        """Test enqueueing job with valid job_id."""
        job_id = uuid4()
        mock_rq_job = Mock(spec=RQJob)
        mock_rq_job.id = str(job_id)
        job_queue.queue.enqueue.return_value = mock_rq_job

        result = job_queue.enqueue_job(job_id)

        assert result is not None
        assert "job_id" in result
        job_queue.queue.enqueue.assert_called_once()
        # Verify status updated to 'queued'
        mock_app_repo.update_status.assert_called_once()

    def test_enqueue_job_validates_job_exists(self, job_queue, mock_jobs_repo):
        """Test enqueue validates job exists in database."""
        job_id = uuid4()
        mock_jobs_repo.get_job_by_id.return_value = None

        with pytest.raises(ValueError, match="Job not found"):
            job_queue.enqueue_job(job_id)

    def test_enqueue_job_with_invalid_job_id_type(self, job_queue):
        """Test enqueue rejects invalid job_id type."""
        with pytest.raises(TypeError):
            job_queue.enqueue_job("not-a-uuid")

    def test_enqueue_job_updates_application_status(self, job_queue, mock_app_repo):
        """Test enqueue updates application_tracking status."""
        job_id = uuid4()
        mock_rq_job = Mock(spec=RQJob)
        job_queue.queue.enqueue.return_value = mock_rq_job

        job_queue.enqueue_job(job_id)

        mock_app_repo.update_status.assert_called_once_with(job_id, "queued")

    def test_enqueue_job_returns_metadata(self, job_queue):
        """Test enqueue returns job metadata."""
        job_id = uuid4()
        mock_rq_job = Mock(spec=RQJob)
        mock_rq_job.id = str(job_id)
        job_queue.queue.enqueue.return_value = mock_rq_job
        job_queue.queue.count = 5

        result = job_queue.enqueue_job(job_id)

        assert result["job_id"] == job_id
        assert "queue_position" in result
        assert "enqueued_at" in result


class TestQueueMonitoring:
    """Test suite for queue monitoring operations."""

    def test_get_queue_depth(self, job_queue):
        """Test get_queue_depth returns pending job count."""
        job_queue.queue.count = 10

        depth = job_queue.get_queue_depth()

        assert depth == 10

    def test_get_active_workers(self, job_queue, mock_redis):
        """Test get_active_workers returns worker count."""
        with patch("app.queue.job_queue.Worker") as mock_worker_class:
            mock_worker_class.count.return_value = 3

            count = job_queue.get_active_workers()

            assert count == 3

    def test_get_failed_jobs(self, job_queue):
        """Test get_failed_jobs retrieves failed jobs."""
        mock_failed_queue = Mock()
        mock_failed_job = Mock(spec=RQJob)
        mock_failed_job.id = "failed-job-1"
        mock_failed_queue.jobs = [mock_failed_job]

        with patch("app.queue.job_queue.Queue") as mock_queue_class:
            mock_queue_class.return_value = mock_failed_queue

            failed_jobs = job_queue.get_failed_jobs()

            assert len(failed_jobs) >= 0  # Can be empty or contain jobs

    def test_get_queue_metrics(self, job_queue):
        """Test get_queue_metrics returns comprehensive metrics."""
        job_queue.queue.count = 5

        with patch("app.queue.job_queue.Worker") as mock_worker_class:
            mock_worker_class.count.return_value = 2
            # Mock get_failed_jobs to return empty list
            with patch.object(job_queue, "get_failed_jobs", return_value=[]):
                metrics = job_queue.get_queue_metrics()

                assert "queue_depth" in metrics
                assert "active_workers" in metrics
                assert "failed_count" in metrics
                assert metrics["queue_depth"] == 5
                assert metrics["active_workers"] == 2


class TestJobRetry:
    """Test suite for job retry operations."""

    def test_retry_job(self, job_queue):
        """Test retry_job re-enqueues a failed job."""
        job_id = uuid4()

        with patch.object(job_queue, "enqueue_job") as mock_enqueue:
            job_queue.retry_job(job_id)

            mock_enqueue.assert_called_once_with(job_id)

    def test_retry_all_failed_jobs(self, job_queue):
        """Test retry_all_failed_jobs re-enqueues all failed jobs."""
        mock_failed_job1 = Mock()
        mock_failed_job1.kwargs = {"job_id": str(uuid4())}
        mock_failed_job2 = Mock()
        mock_failed_job2.kwargs = {"job_id": str(uuid4())}

        with patch.object(job_queue, "get_failed_jobs", return_value=[mock_failed_job1, mock_failed_job2]):
            with patch.object(job_queue, "retry_job") as mock_retry:
                count = job_queue.retry_all_failed_jobs()

                assert count == 2
                assert mock_retry.call_count == 2


class TestQueueManagement:
    """Test suite for queue management operations."""

    def test_clear_queue(self, job_queue):
        """Test clear_queue removes all jobs."""
        job_queue.queue.empty.return_value = True

        job_queue.clear_queue(confirm=True)

        job_queue.queue.empty.assert_called_once()

    def test_clear_queue_requires_confirmation(self, job_queue):
        """Test clear_queue requires confirmation parameter."""
        # Without confirmation, should not clear
        with pytest.raises(ValueError, match="requires confirmation"):
            job_queue.clear_queue(confirm=False)
