"""
DuckDB database connection and management module.

Provides connection pooling and utilities for the job application database.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

import duckdb
from loguru import logger


class DatabaseConnection:
    """Singleton database connection manager for DuckDB."""

    _instance: "DatabaseConnection | None" = None
    _connection: duckdb.DuckDBPyConnection | None = None

    def __new__(cls) -> "DatabaseConnection":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the database connection manager."""
        if self._connection is None:
            self.db_path = self._get_db_path()
            self._ensure_db_directory()
            self._connection = self._create_connection()
            logger.info(f"Database connection initialized: {self.db_path}")

    def _get_db_path(self) -> Path:
        """Get the database file path from environment or use default."""
        # Use in-memory database for tests
        if os.getenv("TESTING", "false").lower() == "true":
            return Path(":memory:")
        db_path_str = os.getenv("DUCKDB_PATH", "data/jobs.duckdb")
        return Path(db_path_str)

    def _ensure_db_directory(self) -> None:
        """Ensure the database directory exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _create_connection(self) -> duckdb.DuckDBPyConnection:
        """Create a new DuckDB connection."""
        try:
            conn = duckdb.connect(str(self.db_path))
            logger.debug(f"DuckDB connection established: {self.db_path}")
            return conn
        except Exception as e:
            logger.error(f"Failed to connect to DuckDB: {e}")
            raise

    @property
    def connection(self) -> duckdb.DuckDBPyConnection:
        """Get the active database connection."""
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection

    def execute(self, query: str, parameters: tuple | None = None) -> duckdb.DuckDBPyConnection:
        """
        Execute a SQL query.

        Args:
            query: SQL query string
            parameters: Optional query parameters

        Returns:
            DuckDB connection with query results
        """
        try:
            if parameters:
                return self.connection.execute(query, parameters)
            return self.connection.execute(query)
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            logger.debug(f"Query: {query}")
            raise

    def fetch_all(self, query: str, parameters: tuple | None = None) -> list:
        """
        Execute a query and fetch all results.

        Args:
            query: SQL query string
            parameters: Optional query parameters

        Returns:
            List of result rows
        """
        result = self.execute(query, parameters)
        return result.fetchall()

    def fetch_one(self, query: str, parameters: tuple | None = None) -> tuple | None:
        """
        Execute a query and fetch one result.

        Args:
            query: SQL query string
            parameters: Optional query parameters

        Returns:
            Single result row or None
        """
        result = self.execute(query, parameters)
        return result.fetchone()

    def close(self) -> None:
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("Database connection closed")


@contextmanager
def get_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Context manager for database connections.

    Yields:
        DuckDB connection
    """
    db = DatabaseConnection()
    try:
        yield db.connection
    except Exception as e:
        logger.error(f"Database operation failed: {e}")
        raise


def create_tables() -> None:
    """
    Create database tables for jobs and application tracking.

    Creates the jobs and application_tracking tables with proper schema.
    """
    db = DatabaseConnection()
    conn = db.connection

    # Create jobs table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id VARCHAR PRIMARY KEY,
            platform_source VARCHAR CHECK(platform_source IN ('linkedin', 'seek', 'indeed')),
            company_name VARCHAR NOT NULL,
            job_title VARCHAR NOT NULL,
            job_url VARCHAR NOT NULL,
            salary_aud_per_day DECIMAL(10,2),
            location VARCHAR,
            posted_date DATE,
            job_description TEXT,
            requirements TEXT,
            responsibilities TEXT,
            discovered_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            duplicate_group_id VARCHAR
        )
    """)
    logger.debug("Jobs table created successfully")

    # Create application_tracking table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS application_tracking (
            application_id VARCHAR PRIMARY KEY,
            job_id VARCHAR NOT NULL,
            status VARCHAR CHECK(status IN (
                'discovered', 'matched', 'documents_generated', 'ready_to_send',
                'sending', 'completed', 'pending', 'failed', 'rejected', 'duplicate'
            )),
            current_stage VARCHAR,
            completed_stages JSON,
            stage_outputs JSON,
            error_info JSON,
            cv_file_path VARCHAR,
            cl_file_path VARCHAR,
            submission_method VARCHAR CHECK(submission_method IN ('email', 'web_form')),
            submitted_timestamp TIMESTAMP,
            contact_person_name VARCHAR,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
        )
    """)
    logger.debug("Application tracking table created successfully")


def create_indexes() -> None:
    """
    Create indexes for database performance optimization.

    Creates unique and composite indexes for common queries.
    """
    db = DatabaseConnection()
    conn = db.connection

    # Create unique index on job_url
    conn.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_jobs_url ON jobs(job_url)
    """)

    # Create composite index on platform_source and posted_date
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_platform_date ON jobs(platform_source, posted_date)
    """)

    # Create index on application status
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_app_status ON application_tracking(status)
    """)

    # Create index on application job_id
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_app_job_id ON application_tracking(job_id)
    """)

    logger.debug("Database indexes created successfully")


def initialize_database() -> None:
    """
    Initialize the database with schema and indexes.

    Creates tables and indexes if they don't exist.
    This is idempotent and can be called multiple times safely.
    """
    db = DatabaseConnection()
    try:
        # Create tables
        create_tables()

        # Create indexes
        create_indexes()

        # Test basic query to verify database is working
        result = db.fetch_one("SELECT 1 as test")
        if result and result[0] == 1:
            logger.info("Database initialization successful")
        else:
            raise RuntimeError("Database test query failed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def get_connection() -> duckdb.DuckDBPyConnection:
    """
    Get the active database connection.

    Returns:
        DuckDB connection instance
    """
    db = DatabaseConnection()
    return db.connection


def get_database_info() -> dict:
    """
    Get information about the database.

    Returns:
        Dictionary with database information
    """
    db = DatabaseConnection()

    # Count tables in database
    table_count = 0
    try:
        result = db.fetch_all(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'main'"
        )
        if result:
            table_count = result[0][0]
    except Exception:
        pass  # Database might not be initialized yet

    return {
        "path": str(db.db_path),
        "exists": db.db_path.exists() if str(db.db_path) != ":memory:" else True,
        "size_bytes": db.db_path.stat().st_size if db.db_path.exists() and str(db.db_path) != ":memory:" else 0,
        "table_count": table_count,
    }


if __name__ == "__main__":
    # Test database initialization
    initialize_database()
    info = get_database_info()
    print(f"Database info: {info}")
