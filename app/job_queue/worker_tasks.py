"""RQ worker tasks for job processing.

This module defines the worker tasks that are executed by RQ workers
to process jobs asynchronously through the agent pipeline.
"""

from typing import Any
from uuid import UUID

from loguru import logger

from app.job_queue.redis_client import get_redis_connection
from app.repositories.application_repository import ApplicationRepository
from app.repositories.database import get_connection
from app.repositories.jobs_repository import JobsRepository
from app.services.job_processor import JobProcessorService


def process_job(job_id: str) -> dict[str, Any]:
    """Process a job through the agent pipeline.

    This is the main RQ worker task that executes asynchronously.
    It coordinates the job processing pipeline and updates application status.

    Args:
        job_id: UUID string of job to process

    Returns:
        Dict containing processing result:
            - status: 'success' or 'failed'
            - job_id: Job ID processed
            - stages_completed: List of agent stages completed
            - error: Error message if failed

    Raises:
        ValueError: If job_id is invalid UUID format
        Exception: If processing fails

    Example:
        >>> # Called by RQ worker
        >>> result = process_job("550e8400-e29b-41d4-a716-446655440000")
        >>> print(result["status"])
        'success'
    """
    try:
        # Validate UUID format
        job_uuid = UUID(job_id)
    except ValueError as e:
        logger.error(f"Invalid job_id format: {job_id}")
        raise ValueError(f"Invalid UUID format: {job_id}") from e

    logger.info(f"Worker processing job: {job_id}")

    # Initialize dependencies
    get_redis_connection()
    db_conn = get_connection()
    jobs_repo = JobsRepository(db_conn)
    app_repo = ApplicationRepository(db_conn)

    # Update status to 'processing'
    app_repo.update_status(job_uuid, "pending")  # Using 'pending' for now
    logger.info(f"Job status updated to 'processing': {job_id}")

    try:
        # Create JobProcessorService and process job
        processor = JobProcessorService(jobs_repository=jobs_repo, application_repository=app_repo)

        result = processor.process_job(job_uuid)

        # Update status based on result
        if result.get("status") == "success":
            app_repo.update_status(job_uuid, "completed")
            logger.info(f"Job processing completed successfully: {job_id}")
        else:
            app_repo.update_status(job_uuid, "failed")
            logger.warning(f"Job processing failed: {job_id}")

        return result

    except Exception as e:
        # Update status to failed and log error
        app_repo.update_status(job_uuid, "failed")
        logger.error(f"Job processing exception: {job_id} - {str(e)}")
        raise


def on_success(job, connection, result):
    """RQ success callback - called when job completes successfully.

    Args:
        job: RQ Job instance
        connection: Redis connection
        result: Return value from worker task
    """
    job_id = job.kwargs.get("job_id", "unknown")
    logger.info(f"RQ job succeeded: {job.id} (job_id={job_id})")


def on_failure(job, connection, type, value, traceback):
    """RQ failure callback - called when job fails.

    Args:
        job: RQ Job instance
        connection: Redis connection
        type: Exception type
        value: Exception value
        traceback: Exception traceback
    """
    job_id = job.kwargs.get("job_id", "unknown")
    logger.error(f"RQ job failed: {job.id} (job_id={job_id}) - {type.__name__}: {value}")
