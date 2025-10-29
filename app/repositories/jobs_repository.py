"""
Jobs repository for CRUD operations on jobs table.

Handles all database operations for job postings.
"""

from loguru import logger

from app.models.job import Job
from app.repositories.database import get_connection


# Whitelist of allowed field names for dynamic SQL queries
# This prevents SQL injection through field names
ALLOWED_FIELDS = {"job_id", "platform_source", "company_name", "job_title", "job_url", "salary_aud_per_day", "location", "posted_date", "job_description", "requirements", "responsibilities", "discovered_timestamp", "duplicate_group_id"}

# Allowed INTERVAL units for parameterized queries
ALLOWED_INTERVAL_UNITS = {"DAY", "HOUR", "MINUTE", "SECOND", "MONTH", "YEAR"}


class InvalidFieldError(ValueError):
    """Raised when an invalid field name is used in dynamic queries."""

    pass


class InvalidIntervalError(ValueError):
    """Raised when an invalid INTERVAL unit is used."""

    pass


class JobsRepository:
    """Repository for job CRUD operations."""

    def __init__(self):
        """Initialize jobs repository."""
        self.conn = get_connection()

    @staticmethod
    def _validate_field_name(field: str) -> None:
        """
        Validate that a field name is in the allowed whitelist.

        Args:
            field: Field name to validate

        Raises:
            InvalidFieldError: If field is not in ALLOWED_FIELDS
        """
        if field not in ALLOWED_FIELDS:
            raise InvalidFieldError(f"Invalid field name '{field}'. Allowed fields: {', '.join(sorted(ALLOWED_FIELDS))}")

    @staticmethod
    def _validate_interval_unit(unit: str) -> None:
        """
        Validate that an INTERVAL unit is allowed.

        Args:
            unit: INTERVAL unit to validate (e.g., 'DAY', 'HOUR')

        Raises:
            InvalidIntervalError: If unit is not in ALLOWED_INTERVAL_UNITS
        """
        unit_upper = unit.upper()
        if unit_upper not in ALLOWED_INTERVAL_UNITS:
            raise InvalidIntervalError(f"Invalid INTERVAL unit '{unit}'. Allowed units: {', '.join(sorted(ALLOWED_INTERVAL_UNITS))}")

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

    def get_job_by_id(self, job_id: str) -> Job | None:
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

    def get_job_by_url(self, job_url: str) -> Job | None:
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

        Raises:
            InvalidFieldError: If any field name is not in the allowed whitelist
        """
        if not updates:
            return

        # Validate all field names before building query
        for field in updates.keys():
            self._validate_field_name(field)

        # Build SET clause dynamically with validated field names
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

    def list_jobs(self, filters: dict | None = None, limit: int = 100, offset: int = 0) -> list[Job]:
        """
        List jobs with optional filtering and pagination.

        Args:
            filters: Dictionary of field filters (e.g., {"platform_source": "linkedin"})
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip (for pagination)

        Returns:
            List of Job instances

        Raises:
            InvalidFieldError: If any filter field name is not in the allowed whitelist
        """
        query = "SELECT * FROM jobs"
        params = []

        # Add WHERE clause if filters provided
        if filters:
            # Validate all field names before building query
            for field in filters.keys():
                self._validate_field_name(field)

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

    def count_jobs(self, filters: dict | None = None) -> int:
        """
        Count jobs with optional filtering.

        Args:
            filters: Dictionary of field filters

        Returns:
            Number of jobs matching filters

        Raises:
            InvalidFieldError: If any filter field name is not in the allowed whitelist
        """
        query = "SELECT COUNT(*) FROM jobs"
        params = []

        if filters:
            # Validate all field names before building query
            for field in filters.keys():
                self._validate_field_name(field)

            where_clauses = []
            for field, value in filters.items():
                where_clauses.append(f"{field} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(where_clauses)

        result = self.conn.execute(query, params).fetchone()
        return result[0] if result else 0

    def get_recent_jobs_by_title(self, title_keywords: list[str], days: int = 30) -> list[Job]:
        """
        Get recent jobs that match title keywords (for duplicate detection pre-filtering).

        Args:
            title_keywords: List of keywords to search for in title
            days: Number of days to look back (default 30)

        Returns:
            List of Job instances matching keywords from last N days

        Raises:
            InvalidIntervalError: If days is not a positive integer
        """
        # Validate days parameter (must be positive integer for INTERVAL)
        if not isinstance(days, int) or days <= 0:
            raise ValueError(f"days must be a positive integer, got {days}")

        # Use parameterized query to prevent INTERVAL injection
        # Build query with LIKE clauses for each keyword
        query = """
            SELECT * FROM jobs
            WHERE discovered_timestamp >= CURRENT_TIMESTAMP - INTERVAL ? DAY
        """

        params = [days]

        if title_keywords:
            # Add OR conditions for each keyword
            keyword_conditions = " OR ".join(["LOWER(job_title) LIKE ?" for _ in title_keywords])
            query += f" AND ({keyword_conditions})"
            # Add wildcards for LIKE matching
            params.extend([f"%{keyword.lower()}%" for keyword in title_keywords])

        query += " ORDER BY discovered_timestamp DESC LIMIT 500"

        try:
            results = self.conn.execute(query, params).fetchall()
            return [Job.from_db_row(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to get recent jobs by title: {e}")
            # Fall back to simpler query without date filter
            query = "SELECT * FROM jobs ORDER BY discovered_timestamp DESC LIMIT 500"
            results = self.conn.execute(query).fetchall()
            return [Job.from_db_row(row) for row in results]
