"""
Jobs repository for CRUD operations on jobs table.

Handles all database operations for job postings.
"""

from typing import Optional
from loguru import logger

from app.models.job import Job
from app.repositories.database import get_connection


class JobsRepository:
    """Repository for job CRUD operations."""

    def __init__(self):
        """Initialize jobs repository."""
        self.conn = get_connection()

    def insert_job(self, job: Job) -> str:
        """
        Insert a new job into the database.

        Args:
            job: Job instance to insert

        Returns:
            The job_id of the inserted job

        Raises:
            Exception: If job_url already exists (unique constraint)
        """
        query = """
            INSERT INTO jobs (
                job_id, platform_source, company_name, job_title,
                job_url, salary_aud_per_day, location, posted_date,
                job_description, requirements, responsibilities,
                discovered_timestamp, duplicate_group_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        job_dict = job.to_dict()
        params = (
            job_dict["job_id"],
            job_dict["platform_source"],
            job_dict["company_name"],
            job_dict["job_title"],
            job_dict["job_url"],
            job_dict["salary_aud_per_day"],
            job_dict["location"],
            job_dict["posted_date"],
            job_dict["job_description"],
            job_dict["requirements"],
            job_dict["responsibilities"],
            job_dict["discovered_timestamp"],
            job_dict["duplicate_group_id"],
        )

        try:
            self.conn.execute(query, params)
            logger.debug(f"Inserted job: {job.job_id} - {job.job_title}")
            return job.job_id
        except Exception as e:
            logger.error(f"Failed to insert job: {e}")
            raise

    def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """
        Retrieve a job by its ID.

        Args:
            job_id: The job ID to retrieve

        Returns:
            Job instance if found, None otherwise
        """
        query = "SELECT * FROM jobs WHERE job_id = ?"
        result = self.conn.execute(query, (job_id,)).fetchone()

        if result:
            return Job.from_db_row(result)
        return None

    def get_job_by_url(self, job_url: str) -> Optional[Job]:
        """
        Retrieve a job by its URL.

        Used for duplicate detection.

        Args:
            job_url: The job URL to search for

        Returns:
            Job instance if found, None otherwise
        """
        query = "SELECT * FROM jobs WHERE job_url = ?"
        result = self.conn.execute(query, (job_url,)).fetchone()

        if result:
            return Job.from_db_row(result)
        return None

    def update_job(self, job_id: str, updates: dict) -> None:
        """
        Update job fields.

        Args:
            job_id: The job ID to update
            updates: Dictionary of fields to update
        """
        if not updates:
            return

        # Build SET clause dynamically
        set_clauses = []
        params = []

        for field, value in updates.items():
            set_clauses.append(f"{field} = ?")
            params.append(value)

        params.append(job_id)

        query = f"UPDATE jobs SET {', '.join(set_clauses)} WHERE job_id = ?"

        try:
            self.conn.execute(query, params)
            logger.debug(f"Updated job: {job_id}")
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")
            raise

    def delete_job(self, job_id: str) -> None:
        """
        Delete a job from the database.

        Note: DuckDB has limitations with foreign keys and doesn't support CASCADE.
        This implementation disables foreign key checks temporarily to delete the job
        and its associated applications.

        Args:
            job_id: The job ID to delete
        """
        try:
            # Disable foreign key checks for this operation
            # DuckDB doesn't support temporary disabling, so we delete in correct order
            # and accept that foreign key constraint may cause issues

            # Delete associated applications first
            delete_apps_query = "DELETE FROM application_tracking WHERE job_id = ?"
            result = self.conn.execute(delete_apps_query, (job_id,))
            apps_deleted = result.fetchone()
            logger.debug(f"Deleted {apps_deleted} applications for job: {job_id}")

            # Then delete the job
            delete_job_query = "DELETE FROM jobs WHERE job_id = ?"
            self.conn.execute(delete_job_query, (job_id,))

            logger.debug(f"Deleted job: {job_id}")
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            raise

    def list_jobs(
        self,
        filters: Optional[dict] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """
        List jobs with optional filtering and pagination.

        Args:
            filters: Dictionary of field filters (e.g., {"platform_source": "linkedin"})
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip (for pagination)

        Returns:
            List of Job instances
        """
        query = "SELECT * FROM jobs"
        params = []

        # Add WHERE clause if filters provided
        if filters:
            where_clauses = []
            for field, value in filters.items():
                where_clauses.append(f"{field} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(where_clauses)

        # Add ORDER BY for consistent pagination
        query += " ORDER BY discovered_timestamp DESC"

        # Add LIMIT and OFFSET
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        results = self.conn.execute(query, params).fetchall()
        return [Job.from_db_row(row) for row in results]

    def count_jobs(self, filters: Optional[dict] = None) -> int:
        """
        Count jobs with optional filtering.

        Args:
            filters: Dictionary of field filters

        Returns:
            Number of jobs matching filters
        """
        query = "SELECT COUNT(*) FROM jobs"
        params = []

        if filters:
            where_clauses = []
            for field, value in filters.items():
                where_clauses.append(f"{field} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(where_clauses)

        result = self.conn.execute(query, params).fetchone()
        return result[0] if result else 0
