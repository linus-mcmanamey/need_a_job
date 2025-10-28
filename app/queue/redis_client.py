"""Redis client module for job queue system.

This module provides Redis connection management with singleton pattern,
health checking, and graceful connection handling.
"""
import os
from typing import Optional
from redis import Redis, ConnectionError as RedisConnectionError
from loguru import logger


# Singleton Redis client instance
_redis_client: Optional[Redis] = None


def get_redis_connection() -> Redis:
    """Get Redis connection using singleton pattern.

    Creates a Redis client on first call and returns the same instance
    on subsequent calls. Configuration is loaded from environment variables.

    Environment Variables:
        REDIS_URL: Full Redis URL (takes precedence if set)
        REDIS_HOST: Redis host (default: localhost)
        REDIS_PORT: Redis port (default: 6379)
        REDIS_DB: Redis database number (default: 0)
        REDIS_PASSWORD: Redis password (optional)

    Returns:
        Redis: Redis client instance with connection pooling

    Example:
        >>> redis = get_redis_connection()
        >>> redis.ping()
        True
    """
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    # Check if REDIS_URL is provided
    redis_url = os.getenv("REDIS_URL")

    if redis_url:
        logger.info(f"Connecting to Redis using REDIS_URL")
        _redis_client = Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    else:
        # Use individual environment variables
        host = os.getenv("REDIS_HOST", "localhost")
        port = int(os.getenv("REDIS_PORT", "6379"))
        db = int(os.getenv("REDIS_DB", "0"))
        password = os.getenv("REDIS_PASSWORD", None)

        logger.info(f"Connecting to Redis at {host}:{port} (db={db})")

        _redis_client = Redis(
            host=host,
            port=port,
            db=db,
            password=password if password else None,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )

    return _redis_client


def check_redis_health() -> bool:
    """Check Redis connection health.

    Attempts to ping Redis server to verify connectivity.
    Handles connection errors gracefully and returns status.

    Returns:
        bool: True if Redis is responsive, False otherwise

    Example:
        >>> if check_redis_health():
        ...     print("Redis is healthy")
        ... else:
        ...     print("Redis connection failed")
    """
    try:
        redis = get_redis_connection()
        redis.ping()
        logger.debug("Redis health check passed")
        return True
    except RedisConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        return False
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False


def close_redis_connection() -> None:
    """Close Redis connection and cleanup resources.

    Closes the singleton Redis client and resets the global reference.
    Safe to call even if connection is not established.

    Example:
        >>> close_redis_connection()
        >>> # Connection closed and cleaned up
    """
    global _redis_client

    if _redis_client is not None:
        try:
            _redis_client.close()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        finally:
            _redis_client = None
    else:
        logger.debug("No Redis connection to close")
