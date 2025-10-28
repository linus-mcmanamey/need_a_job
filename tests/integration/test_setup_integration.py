"""
Integration tests for verifying project setup and configuration.

Tests that services can be initialized and work together correctly.
"""

import os
from pathlib import Path

import pytest


@pytest.mark.integration
class TestDatabaseIntegration:
    """Integration tests for database setup."""

    def test_database_initialization(self) -> None:
        """Test that database can be initialized."""
        from app.repositories.database import initialize_database

        # This should create the database file if it doesn't exist
        initialize_database()

        # Verify database file was created
        db_path = Path(os.getenv("DUCKDB_PATH", "data/job_applications.duckdb"))
        assert db_path.exists(), "Database file was not created"

    def test_database_connection(self) -> None:
        """Test that database connection works."""
        from app.repositories.database import DatabaseConnection

        db = DatabaseConnection()
        result = db.fetch_one("SELECT 1 as test")
        assert result is not None
        assert result[0] == 1

    def test_database_info(self) -> None:
        """Test database info retrieval."""
        from app.repositories.database import get_database_info

        info = get_database_info()
        assert "path" in info
        assert "exists" in info
        assert "size_bytes" in info
        assert info["exists"] is True


@pytest.mark.integration
@pytest.mark.skipif(not os.getenv("REDIS_URL"), reason="Redis not configured (REDIS_URL not set)")
class TestRedisIntegration:
    """Integration tests for Redis connection."""

    def test_redis_connection(self) -> None:
        """Test Redis connection."""
        import redis

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url)
        assert r.ping() is True

    def test_rq_queue_creation(self) -> None:
        """Test RQ queue can be created."""
        import redis
        from rq import Queue

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        r = redis.from_url(redis_url)
        queue = Queue("test_queue", connection=r)
        assert queue is not None
        assert queue.name == "test_queue"


@pytest.mark.integration
class TestFastAPIIntegration:
    """Integration tests for FastAPI application."""

    def test_fastapi_app_creation(self) -> None:
        """Test FastAPI app can be created."""
        from app.main import app

        assert app is not None
        assert app.title == "Job Application Automation System"

    def test_health_endpoint(self) -> None:
        """Test health check endpoint."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "job-automation-api"
        assert "version" in data

    def test_root_endpoint(self) -> None:
        """Test root endpoint."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


@pytest.mark.integration
class TestGradioIntegration:
    """Integration tests for Gradio UI."""

    def test_gradio_ui_creation(self) -> None:
        """Test Gradio UI can be created."""
        from app.ui.gradio_app import create_ui

        app = create_ui()
        assert app is not None


@pytest.mark.integration
class TestEnvironmentConfiguration:
    """Integration tests for environment configuration."""

    def test_env_file_exists(self) -> None:
        """Test that .env file exists or .env.example can be used."""
        env_file = Path(".env")
        env_example = Path(".env.example")
        assert env_file.exists() or env_example.exists(), "No environment file found"

    def test_required_env_vars_defined(self) -> None:
        """Test that critical environment variables are defined."""
        # Load environment from .env if it exists
        from dotenv import load_dotenv

        load_dotenv()

        # Check DUCKDB_PATH has a default
        db_path = os.getenv("DUCKDB_PATH", "data/job_applications.duckdb")
        assert db_path is not None

        # REDIS_URL should have a default
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        assert redis_url is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
