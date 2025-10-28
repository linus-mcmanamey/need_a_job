"""Queue module for Redis-based job processing with RQ."""

from app.queue.redis_client import check_redis_health, close_redis_connection, get_redis_connection

__all__ = ["get_redis_connection", "check_redis_health", "close_redis_connection"]

# Import other modules when they exist
try:
    from app.queue.job_queue import JobQueue

    __all__.append("JobQueue")
except ImportError:
    pass

try:
    from app.queue.worker_tasks import process_job

    __all__.append("process_job")
except ImportError:
    pass
