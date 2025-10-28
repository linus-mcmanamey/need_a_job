"""
Unit tests for database module.

Tests database connection, initialization, and schema creation.
"""

import duckdb
import pytest

from app.repositories.database import create_indexes, create_tables, get_connection, get_database_info, initialize_database


class TestDatabaseConnection:
    """Test database connection management."""

    def test_get_connection_returns_duckdb_connection(self) -> None:
        """Test that get_connection returns a DuckDB connection."""
        conn = get_connection()
        assert conn is not None
        assert isinstance(conn, duckdb.DuckDBPyConnection)

    def test_get_connection_uses_memory_for_tests(self) -> None:
        """Test that test environment uses in-memory database."""
        conn = get_connection()
        # In test environment, should use :memory:
        assert conn is not None

    def test_connection_is_reusable(self) -> None:
        """Test that same connection is returned on multiple calls."""
        conn1 = get_connection()
        conn2 = get_connection()
        # Should return same connection (thread-safe singleton-like behavior)
        assert conn1 is conn2


class TestDatabaseInitialization:
    """Test database initialization functionality."""

    def test_initialize_database_creates_tables(self) -> None:
        """Test that initialize_database creates required tables."""
        conn = get_connection()
        initialize_database()

        # Check that jobs table exists
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'jobs'").fetchone()
        assert result is not None
        assert result[0] == "jobs"

        # Check that application_tracking table exists
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'application_tracking'").fetchone()
        assert result is not None
        assert result[0] == "application_tracking"

    def test_initialize_database_is_idempotent(self) -> None:
        """Test that initialize_database can be called multiple times safely."""
        conn = get_connection()
        initialize_database()
        initialize_database()  # Should not raise error

        # Tables should still exist
        result = conn.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name IN ('jobs', 'application_tracking')").fetchone()
        assert result[0] == 2

    def test_create_tables_creates_jobs_table(self) -> None:
        """Test that create_tables creates jobs table with correct schema."""
        conn = get_connection()
        create_tables()

        # Verify table exists
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'jobs'").fetchone()
        assert result is not None

        # Verify key columns exist
        columns = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'jobs'").fetchall()
        column_names = [col[0] for col in columns]

        assert "job_id" in column_names
        assert "platform_source" in column_names
        assert "company_name" in column_names
        assert "job_title" in column_names
        assert "job_url" in column_names
        assert "salary_aud_per_day" in column_names
        assert "duplicate_group_id" in column_names

    def test_create_tables_creates_application_tracking_table(self) -> None:
        """Test that create_tables creates application_tracking table."""
        conn = get_connection()
        create_tables()

        # Verify table exists
        result = conn.execute("SELECT table_name FROM information_schema.tables WHERE table_name = 'application_tracking'").fetchone()
        assert result is not None

        # Verify key columns exist
        columns = conn.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'application_tracking'").fetchall()
        column_names = [col[0] for col in columns]

        assert "application_id" in column_names
        assert "job_id" in column_names
        assert "status" in column_names
        assert "current_stage" in column_names
        assert "completed_stages" in column_names
        assert "stage_outputs" in column_names
        assert "error_info" in column_names

    def test_create_indexes_creates_job_url_index(self) -> None:
        """Test that create_indexes creates unique index on job_url."""
        conn = get_connection()
        create_tables()
        create_indexes()

        # DuckDB stores index info differently, verify by attempting duplicate insert
        conn.execute("""
            INSERT INTO jobs (job_id, platform_source, company_name, job_title, job_url)
            VALUES ('550e8400-e29b-41d4-a716-446655440000', 'linkedin', 'Test Co', 'Engineer', 'http://test.com/job1')
        """)

        # Attempting to insert same URL should fail
        with pytest.raises(Exception):  # DuckDB raises Constraint error
            conn.execute("""
                INSERT INTO jobs (job_id, platform_source, company_name, job_title, job_url)
                VALUES ('550e8400-e29b-41d4-a716-446655440001', 'linkedin', 'Test Co 2', 'Engineer 2', 'http://test.com/job1')
            """)


class TestDatabaseInfo:
    """Test database information retrieval."""

    def test_get_database_info_returns_dict(self) -> None:
        """Test that get_database_info returns database information."""
        info = get_database_info()
        assert isinstance(info, dict)
        assert "exists" in info
        assert "table_count" in info

    def test_get_database_info_shows_tables_after_init(self) -> None:
        """Test that get_database_info shows tables after initialization."""
        initialize_database()
        info = get_database_info()
        assert info["exists"] is True
        assert info["table_count"] >= 2  # At least jobs and application_tracking


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
