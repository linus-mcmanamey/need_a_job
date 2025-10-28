#!/usr/bin/env python3
"""Start RQ worker for job processing.

This script starts an RQ worker that processes jobs from the queue.
Multiple workers can be run concurrently for parallel processing.

Usage:
    python scripts/run_worker.py
    python scripts/run_worker.py --name worker-1
    python scripts/run_worker.py --burst  # Exit after processing all jobs
"""
import argparse
import sys
from loguru import logger
from rq import Worker

from app.queue.redis_client import get_redis_connection, check_redis_health


def main():
    """Start RQ worker."""
    parser = argparse.ArgumentParser(description="Start RQ worker for job processing")
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Worker name (default: auto-generated)",
    )
    parser.add_argument(
        "--burst",
        action="store_true",
        help="Exit after processing all jobs (for testing)",
    )
    parser.add_argument(
        "--queue",
        type=str,
        default="job_processing_queue",
        help="Queue name to process (default: job_processing_queue)",
    )

    args = parser.parse_args()

    # Check Redis health
    logger.info("Checking Redis connection...")
    if not check_redis_health():
        logger.error("Redis connection failed. Ensure Redis is running.")
        sys.exit(1)

    logger.info("Redis connection successful")

    # Get Redis connection
    redis = get_redis_connection()

    # Create worker
    worker = Worker(
        queues=[args.queue],
        connection=redis,
        name=args.name,
    )

    logger.info(f"Starting worker: {worker.name}")
    logger.info(f"Listening to queue: {args.queue}")

    if args.burst:
        logger.info("Burst mode: Worker will exit after processing all jobs")

    # Start worker
    try:
        worker.work(burst=args.burst)
    except KeyboardInterrupt:
        logger.info("Worker interrupted by user")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)

    logger.info("Worker stopped")


if __name__ == "__main__":
    main()
