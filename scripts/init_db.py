#!/usr/bin/env python3
"""
Database initialization script.

Creates DuckDB database with schema and indexes.
Can be run standalone or imported.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

from app.repositories.database import get_database_info, initialize_database


def init_database(reset: bool = False) -> None:
    """
    Initialize the database.

    Args:
        reset: If True, drop existing tables and recreate (WARNING: data loss)
    """
    if reset:
        logger.warning("Reset flag set - this will drop all existing data!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Database reset cancelled")
            return

        # Drop tables if reset requested
        from app.repositories.database import get_connection

        conn = get_connection()
        try:
            conn.execute("DROP TABLE IF EXISTS application_tracking CASCADE")
            conn.execute("DROP TABLE IF EXISTS jobs CASCADE")
            logger.info("Existing tables dropped")
        except Exception as e:
            logger.error(f"Error dropping tables: {e}")
            raise

    # Initialize database (creates tables and indexes)
    try:
        initialize_database()
        logger.info("✅ Database initialized successfully")

        # Show database info
        info = get_database_info()
        logger.info(f"Database path: {info['path']}")
        logger.info(f"Table count: {info['table_count']}")
        if info["size_bytes"] > 0:
            size_mb = info["size_bytes"] / (1024 * 1024)
            logger.info(f"Database size: {size_mb:.2f} MB")

    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        sys.exit(1)


def main():
    """Main CLI interface for database initialization."""
    parser = argparse.ArgumentParser(
        description="Initialize DuckDB database for job application system"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop existing tables and recreate (WARNING: destroys all data)",
    )

    args = parser.parse_args()

    logger.info("🚀 Starting database initialization...")
    init_database(reset=args.reset)
    logger.info("✨ Database ready for use!")


if __name__ == "__main__":
    main()
