"""
Pytest configuration for repository unit tests.

Sets up test environment and fixtures.
"""

import pytest


@pytest.fixture(scope="function", autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("TESTING", "true")

    # Reset the DatabaseConnection singleton before each test
    from app.repositories.database import DatabaseConnection

    DatabaseConnection._instance = None
    DatabaseConnection._connection = None

    yield

    # Clean up after test
    DatabaseConnection._instance = None
    DatabaseConnection._connection = None
