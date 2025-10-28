#!/usr/bin/env python3
"""Retry failed jobs from dead letter queue.

This script re-enqueues failed jobs for another processing attempt.
Useful for recovering from temporary failures.

Usage:
    python scripts/retry_failed_jobs.py --all
    python scripts/retry_failed_jobs.py --job-id <uuid>
"""

import argparse
from uuid import UUID

from loguru import logger

from app.queue.job_queue import JobQueue
from app.queue.redis_client import get_redis_connection
from app.repositories.application_repository import ApplicationRepository
from app.repositories.database import get_connection
from app.repositories.jobs_repository import JobsRepository


def main():
    """Retry failed jobs."""
    parser = argparse.ArgumentParser(description="Retry failed jobs")
    parser.add_argument("--all", action="store_true", help="Retry all failed jobs")
    parser.add_argument("--job-id", type=str, help="Retry specific job by UUID")

    args = parser.parse_args()

    if not args.all and not args.job_id:
        parser.error("Must specify --all or --job-id")

    logger.info("Initializing failed job retry...")

    # Initialize dependencies
    redis = get_redis_connection()
    db_conn = get_connection()
    jobs_repo = JobsRepository(db_conn)
    app_repo = ApplicationRepository(db_conn)

    # Create JobQueue
    job_queue = JobQueue(redis_connection=redis, jobs_repository=jobs_repo, application_repository=app_repo)

    if args.all:
        # Retry all failed jobs
        logger.info("Retrying all failed jobs...")
        count = job_queue.retry_all_failed_jobs()
        logger.info(f"Retried {count} failed jobs")

    elif args.job_id:
        # Retry specific job
        try:
            job_uuid = UUID(args.job_id)
            logger.info(f"Retrying job: {job_uuid}")
            job_queue.retry_job(job_uuid)
            logger.info("Job re-enqueued successfully")
        except ValueError:
            logger.error(f"Invalid UUID format: {args.job_id}")
        except Exception as e:
            logger.error(f"Failed to retry job: {e}")


if __name__ == "__main__":
    main()
