"""
Pytest configuration for repository integration tests.

Sets up integration test environment with database cleanup.
"""

from pathlib import Path

import pytest


@pytest.fixture(scope="function", autouse=True)
def setup_integration_test_environment(monkeypatch):
    """Set up integration test environment with clean database."""
    # Use a test database file for integration tests
    test_db_path = "data/test_jobs.duckdb"
    monkeypatch.setenv("DUCKDB_PATH", test_db_path)

    # Reset the DatabaseConnection singleton before each test
    from app.repositories.database import DatabaseConnection

    DatabaseConnection._instance = None
    DatabaseConnection._connection = None

    yield

    # Clean up: close connection and delete test database file
    DatabaseConnection._instance = None
    if DatabaseConnection._connection:
        DatabaseConnection._connection.close()
    DatabaseConnection._connection = None

    # Remove test database file
    db_file = Path(test_db_path)
    if db_file.exists():
        db_file.unlink()
