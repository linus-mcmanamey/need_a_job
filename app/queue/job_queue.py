"""JobQueue class for managing Redis-based job queue operations.

This module provides the JobQueue class for enqueueing jobs, monitoring
queue status, and managing job lifecycle.
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID
from redis import Redis
from rq import Queue
from rq.job import Job as RQJob
from rq.worker import Worker
from loguru import logger

from app.repositories.jobs_repository import JobsRepository
from app.repositories.application_repository import ApplicationRepository


class JobQueue:
    """Job queue manager for Redis-based asynchronous job processing.

    Manages job enqueueing, monitoring, and lifecycle operations using
    Redis Queue (RQ) library. Integrates with job and application repositories
    for validation and status tracking.

    Attributes:
        redis: Redis client connection
        jobs_repo: Repository for job data access
        app_repo: Repository for application tracking
        queue: RQ Queue instance for job processing
    """

    def __init__(
        self,
        redis_connection: Redis,
        jobs_repository: JobsRepository,
        application_repository: ApplicationRepository,
        queue_name: str = "job_processing_queue",
    ):
        """Initialize JobQueue with dependencies.

        Args:
            redis_connection: Redis client instance
            jobs_repository: JobsRepository for job validation
            application_repository: ApplicationRepository for status tracking
            queue_name: Name of the RQ queue (default: job_processing_queue)
        """
        self.redis = redis_connection
        self.jobs_repo = jobs_repository
        self.app_repo = application_repository
        self.queue_name = queue_name

        # Create RQ Queue
        self.queue = Queue(name=queue_name, connection=redis_connection)

        logger.info(f"JobQueue initialized: queue='{queue_name}'")

    def enqueue_job(self, job_id: UUID) -> Dict[str, Any]:
        """Enqueue a job for processing by worker.

        Validates job exists in database, enqueues job for processing,
        and updates application tracking status to 'queued'.

        Args:
            job_id: UUID of job to enqueue

        Returns:
            Dict containing job metadata:
                - job_id: UUID of enqueued job
                - rq_job_id: RQ job identifier
                - queue_position: Position in queue
                - enqueued_at: Timestamp of enqueue

        Raises:
            TypeError: If job_id is not a UUID
            ValueError: If job not found in database

        Example:
            >>> queue = JobQueue(redis, jobs_repo, app_repo)
            >>> result = queue.enqueue_job(job_id)
            >>> print(f"Job enqueued at position {result['queue_position']}")
        """
        if not isinstance(job_id, UUID):
            raise TypeError(f"job_id must be UUID, got {type(job_id)}")

        # Validate job exists
        job = self.jobs_repo.get_job_by_id(job_id)
        if job is None:
            raise ValueError(f"Job not found: {job_id}")

        # Enqueue job for processing
        rq_job = self.queue.enqueue(
            "app.queue.worker_tasks.process_job",
            job_id=str(job_id),
            job_timeout=600,  # 10 minutes
            result_ttl=86400,  # 24 hours
            failure_ttl=86400 * 7,  # 7 days
        )

        # Update application status to queued
        self.app_repo.update_status(job_id, "queued")

        logger.info(
            f"Job enqueued: job_id={job_id}, rq_job_id={rq_job.id}, "
            f"queue_depth={self.queue.count}"
        )

        return {
            "job_id": job_id,
            "rq_job_id": rq_job.id,
            "queue_position": self.queue.count,
            "enqueued_at": datetime.utcnow(),
        }

    def get_queue_depth(self) -> int:
        """Get number of pending jobs in queue.

        Returns:
            int: Number of jobs waiting to be processed

        Example:
            >>> depth = queue.get_queue_depth()
            >>> print(f"{depth} jobs pending")
        """
        depth = self.queue.count
        logger.debug(f"Queue depth: {depth}")
        return depth

    def get_active_workers(self) -> int:
        """Get number of active workers processing jobs.

        Returns:
            int: Number of active RQ workers

        Example:
            >>> workers = queue.get_active_workers()
            >>> print(f"{workers} workers active")
        """
        workers = Worker.count(connection=self.redis)
        logger.debug(f"Active workers: {workers}")
        return workers

    def get_failed_jobs(self) -> List[RQJob]:
        """Get list of failed jobs from dead letter queue.

        Returns:
            List[RQJob]: List of failed RQ job instances

        Example:
            >>> failed = queue.get_failed_jobs()
            >>> for job in failed:
            ...     print(f"Failed: {job.id}")
        """
        failed_queue = Queue(name="failed", connection=self.redis)
        failed_jobs = failed_queue.jobs
        logger.debug(f"Failed jobs: {len(failed_jobs)}")
        return list(failed_jobs)

    def get_queue_metrics(self) -> Dict[str, Any]:
        """Get comprehensive queue metrics.

        Returns:
            Dict containing:
                - queue_depth: Pending jobs count
                - active_workers: Number of workers
                - failed_count: Number of failed jobs
                - queue_name: Name of queue

        Example:
            >>> metrics = queue.get_queue_metrics()
            >>> print(f"Queue: {metrics['queue_depth']} pending, "
            ...       f"{metrics['active_workers']} workers")
        """
        metrics = {
            "queue_name": self.queue_name,
            "queue_depth": self.get_queue_depth(),
            "active_workers": self.get_active_workers(),
            "failed_count": len(self.get_failed_jobs()),
            "timestamp": datetime.utcnow(),
        }

        logger.debug(f"Queue metrics: {metrics}")
        return metrics

    def retry_job(self, job_id: UUID) -> None:
        """Retry a failed job by re-enqueueing it.

        Args:
            job_id: UUID of job to retry

        Example:
            >>> queue.retry_job(failed_job_id)
        """
        logger.info(f"Retrying job: {job_id}")
        self.enqueue_job(job_id)

    def retry_all_failed_jobs(self) -> int:
        """Retry all jobs in failed queue.

        Returns:
            int: Number of jobs re-enqueued

        Example:
            >>> count = queue.retry_all_failed_jobs()
            >>> print(f"Retried {count} failed jobs")
        """
        failed_jobs = self.get_failed_jobs()
        count = 0

        for rq_job in failed_jobs:
            try:
                job_id_str = rq_job.kwargs.get("job_id")
                if job_id_str:
                    job_id = UUID(job_id_str)
                    self.retry_job(job_id)
                    count += 1
            except Exception as e:
                logger.error(f"Failed to retry job {rq_job.id}: {e}")

        logger.info(f"Retried {count} failed jobs")
        return count

    def clear_queue(self, confirm: bool = False) -> None:
        """Clear all jobs from queue (DESTRUCTIVE - use carefully).

        Args:
            confirm: Must be True to proceed (safety check)

        Raises:
            ValueError: If confirm is not True

        Example:
            >>> queue.clear_queue(confirm=True)  # Clears all jobs
        """
        if not confirm:
            raise ValueError("clear_queue requires confirmation (confirm=True)")

        self.queue.empty()
        logger.warning(f"Queue cleared: {self.queue_name}")
