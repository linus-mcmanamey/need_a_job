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
        db_path_str = os.getenv("DUCKDB_PATH", "data/job_applications.duckdb")
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


def initialize_database() -> None:
    """
    Initialize the database and create the file if it doesn't exist.

    This function ensures the database file is created and accessible.
    Schema initialization will be handled in a separate migration system.
    """
    db = DatabaseConnection()
    try:
        # Test basic query to verify database is working
        result = db.fetch_one("SELECT 1 as test")
        if result and result[0] == 1:
            logger.info("Database initialization successful")
        else:
            raise RuntimeError("Database test query failed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def get_database_info() -> dict:
    """
    Get information about the database.

    Returns:
        Dictionary with database information
    """
    db = DatabaseConnection()
    return {
        "path": str(db.db_path),
        "exists": db.db_path.exists(),
        "size_bytes": db.db_path.stat().st_size if db.db_path.exists() else 0,
    }


if __name__ == "__main__":
    # Test database initialization
    initialize_database()
    info = get_database_info()
    print(f"Database info: {info}")
