#!/usr/bin/env python3
"""Monitor job queue status and metrics.

This script displays real-time metrics about the job queue including
pending jobs, active workers, and failed jobs.

Usage:
    python scripts/monitor_queue.py
    python scripts/monitor_queue.py --watch  # Continuous monitoring
"""

import argparse
import time

from loguru import logger

from app.queue.job_queue import JobQueue
from app.queue.redis_client import get_redis_connection
from app.repositories.application_repository import ApplicationRepository
from app.repositories.database import get_connection
from app.repositories.jobs_repository import JobsRepository


def display_metrics(job_queue: JobQueue):
    """Display queue metrics."""
    metrics = job_queue.get_queue_metrics()

    print("\n" + "=" * 60)
    print(f"Queue Metrics - {metrics['timestamp']}")
    print("=" * 60)
    print(f"Queue Name:      {metrics['queue_name']}")
    print(f"Queue Depth:     {metrics['queue_depth']} jobs pending")
    print(f"Active Workers:  {metrics['active_workers']} workers")
    print(f"Failed Jobs:     {metrics['failed_count']} jobs")
    print("=" * 60)


def main():
    """Monitor queue."""
    parser = argparse.ArgumentParser(description="Monitor job queue status")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Continuously monitor (refresh every 5 seconds)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Refresh interval in seconds (default: 5)",
    )

    args = parser.parse_args()

    logger.info("Initializing queue monitor...")

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

    if args.watch:
        logger.info(f"Starting continuous monitoring (refresh every {args.interval}s)")
        logger.info("Press Ctrl+C to stop")

        try:
            while True:
                display_metrics(job_queue)
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
    else:
        # Single snapshot
        display_metrics(job_queue)


if __name__ == "__main__":
    main()
