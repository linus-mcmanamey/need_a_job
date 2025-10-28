#!/usr/bin/env python3
"""Clear all jobs from queue.

CAUTION: This is a destructive operation that removes all pending jobs.
Use with care, primarily for testing and development.

Usage:
    python scripts/clear_queue.py --confirm
"""
import argparse
import sys
from loguru import logger

from app.queue.redis_client import get_redis_connection
from app.queue.job_queue import JobQueue
from app.repositories.database import get_connection
from app.repositories.jobs_repository import JobsRepository
from app.repositories.application_repository import ApplicationRepository


def main():
    """Clear queue."""
    parser = argparse.ArgumentParser(description="Clear all jobs from queue")
    parser.add_argument(
        "--confirm",
        action="store_true",
        required=True,
        help="Confirmation required (safety check)",
    )

    args = parser.parse_args()

    if not args.confirm:
        logger.error("Must use --confirm flag to clear queue")
        sys.exit(1)

    logger.warning("Clearing job queue...")

    # Initialize dependencies
    redis = get_redis_connection()
    db_conn = get_connection()
    jobs_repo = JobsRepository(db_conn)
    app_repo = ApplicationRepository(db_conn)

    # Create JobQueue
    job_queue = JobQueue(
        redis_connection=redis,
        jobs_repository=jobs_repo,
        application_repository=app_repo,
    )

    # Get queue depth before clearing
    depth_before = job_queue.get_queue_depth()

    # Clear queue
    job_queue.clear_queue(confirm=True)

    depth_after = job_queue.get_queue_depth()

    logger.info(f"Queue cleared: {depth_before} jobs removed")
    logger.info(f"Queue depth now: {depth_after}")


if __name__ == "__main__":
    main()
