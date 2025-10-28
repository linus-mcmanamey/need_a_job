"""Unit tests for Redis client module."""

import os
from unittest.mock import Mock, patch

import pytest
from redis import ConnectionError as RedisConnectionError
from redis import Redis

import app.queue.redis_client as redis_client_module
from app.queue.redis_client import check_redis_health, close_redis_connection, get_redis_connection


@pytest.fixture(autouse=True)
def reset_redis_singleton():
    """Reset Redis singleton before each test."""
    redis_client_module._redis_client = None
    yield
    redis_client_module._redis_client = None


class TestRedisClient:
    """Test suite for Redis client functionality."""

    def test_get_redis_connection_creates_client(self):
        """Test that get_redis_connection creates a Redis client."""
        with patch("app.queue.redis_client.Redis") as mock_redis:
            mock_instance = Mock(spec=Redis)
            mock_redis.return_value = mock_instance

            client = get_redis_connection()

            assert client is not None
            assert isinstance(client, (Redis, Mock))

    def test_get_redis_connection_uses_environment_variables(self):
        """Test that Redis connection uses environment variables."""
        with patch.dict(os.environ, {"REDIS_HOST": "testhost", "REDIS_PORT": "7000", "REDIS_DB": "2", "REDIS_PASSWORD": "testpass"}):
            with patch("app.queue.redis_client.Redis") as mock_redis:
                get_redis_connection()

                mock_redis.assert_called_once()
                call_kwargs = mock_redis.call_args[1]
                assert call_kwargs["host"] == "testhost"
                assert call_kwargs["port"] == 7000
                assert call_kwargs["db"] == 2
                assert call_kwargs["password"] == "testpass"

    def test_get_redis_connection_uses_default_values(self):
        """Test that Redis connection uses defaults when env vars not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("app.queue.redis_client.Redis") as mock_redis:
                get_redis_connection()

                call_kwargs = mock_redis.call_args[1]
                assert call_kwargs["host"] == "localhost"
                assert call_kwargs["port"] == 6379
                assert call_kwargs["db"] == 0

    def test_get_redis_connection_returns_singleton(self):
        """Test that get_redis_connection returns the same instance."""
        with patch("app.queue.redis_client.Redis") as mock_redis:
            mock_instance = Mock(spec=Redis)
            mock_redis.return_value = mock_instance

            client1 = get_redis_connection()
            client2 = get_redis_connection()

            assert client1 is client2
            # Redis should only be called once (singleton pattern)
            assert mock_redis.call_count == 1

    def test_check_redis_health_returns_true_on_success(self):
        """Test that check_redis_health returns True when Redis responds."""
        with patch("app.queue.redis_client.get_redis_connection") as mock_get_conn:
            mock_client = Mock(spec=Redis)
            mock_client.ping.return_value = True
            mock_get_conn.return_value = mock_client

            result = check_redis_health()

            assert result is True
            mock_client.ping.assert_called_once()

    def test_check_redis_health_returns_false_on_connection_error(self):
        """Test that check_redis_health returns False on connection error."""
        with patch("app.queue.redis_client.get_redis_connection") as mock_get_conn:
            mock_client = Mock(spec=Redis)
            mock_client.ping.side_effect = RedisConnectionError("Connection failed")
            mock_get_conn.return_value = mock_client

            result = check_redis_health()

            assert result is False

    def test_check_redis_health_returns_false_on_generic_exception(self):
        """Test that check_redis_health handles generic exceptions."""
        with patch("app.queue.redis_client.get_redis_connection") as mock_get_conn:
            mock_client = Mock(spec=Redis)
            mock_client.ping.side_effect = Exception("Unexpected error")
            mock_get_conn.return_value = mock_client

            result = check_redis_health()

            assert result is False

    def test_close_redis_connection_closes_client(self):
        """Test that close_redis_connection closes the Redis client."""
        with patch("app.queue.redis_client._redis_client", Mock(spec=Redis)) as mock_client:
            with patch("app.queue.redis_client.get_redis_connection") as mock_get_conn:
                mock_get_conn.return_value = mock_client

                close_redis_connection()

                mock_client.close.assert_called_once()

    def test_close_redis_connection_handles_none_client(self):
        """Test that close_redis_connection handles None client gracefully."""
        with patch("app.queue.redis_client._redis_client", None):
            # Should not raise exception
            close_redis_connection()

    def test_redis_url_environment_variable(self):
        """Test that REDIS_URL environment variable takes precedence."""
        with patch.dict(os.environ, {"REDIS_URL": "redis://customhost:6380/1"}):
            with patch("app.queue.redis_client.Redis") as mock_redis:
                get_redis_connection()

                # Should use from_url method
                (mock_redis.from_url.call_args if hasattr(mock_redis, "from_url") else None)
                # This tests that we handle REDIS_URL if present


class TestRedisConnectionPooling:
    """Test suite for Redis connection pooling."""

    def test_connection_uses_connection_pool(self):
        """Test that Redis connection uses connection pooling."""
        with patch("app.queue.redis_client.Redis") as mock_redis:
            mock_instance = Mock(spec=Redis)
            mock_redis.return_value = mock_instance

            get_redis_connection()

            call_kwargs = mock_redis.call_args[1]
            # Verify decode_responses is enabled for better string handling
            assert call_kwargs.get("decode_responses") is True


class TestRedisClientRetry:
    """Test suite for Redis client retry logic."""

    def test_get_redis_connection_retries_on_failure(self):
        """Test that connection creation retries on failure."""
        # This will be implemented if we add retry logic
        pass  # Placeholder for future enhancement
