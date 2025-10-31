"""
Application repository for CRUD operations on application_tracking table.

Handles all database operations for application tracking through the agent pipeline.
"""

from loguru import logger

from app.models.application import Application
from app.repositories.database import get_connection


class ApplicationRepository:
    """Repository for application tracking CRUD operations."""

    def __init__(self):
        """Initialize application repository."""
        self.conn = get_connection()

    def insert_application(self, application: Application) -> str:
        """
        Insert a new application into the database.

        Args:
            application: Application instance to insert

        Returns:
            The application_id of the inserted application

        Raises:
            Exception: If foreign key constraint fails (invalid job_id)
        """
        query = """
            INSERT INTO application_tracking (
                application_id, job_id, status, current_stage,
                completed_stages, stage_outputs, error_info,
                cv_file_path, cl_file_path, submission_method,
                submitted_timestamp, contact_person_name,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        app_dict = application.to_dict()
        params = (
            app_dict["application_id"],
            app_dict["job_id"],
            app_dict["status"],
            app_dict["current_stage"],
            app_dict["completed_stages"],
            app_dict["stage_outputs"],
            app_dict["error_info"],
            app_dict["cv_file_path"],
            app_dict["cl_file_path"],
            app_dict["submission_method"],
            app_dict["submitted_timestamp"],
            app_dict["contact_person_name"],
            app_dict["created_at"],
            app_dict["updated_at"],
        )

        try:
            self.conn.execute(query, params)
            logger.debug(f"Inserted application: {application.application_id}")
            return application.application_id
        except Exception as e:
            logger.error(f"Failed to insert application: {e}")
            raise

    def get_application_by_id(self, application_id: str) -> Application | None:
        """
        Retrieve an application by its ID.

        Args:
            application_id: The application ID to retrieve

        Returns:
            Application instance if found, None otherwise
        """
        query = "SELECT * FROM application_tracking WHERE application_id = ?"
        result = self.conn.execute(query, (application_id,)).fetchone()

        if result:
            return Application.from_db_row(result)
        return None

    def get_application_by_job_id(self, job_id: str) -> Application | None:
        """
        Retrieve an application by job ID.

        Args:
            job_id: The job ID to search for

        Returns:
            Application instance if found, None otherwise
        """
        query = "SELECT * FROM application_tracking WHERE job_id = ? LIMIT 1"
        result = self.conn.execute(query, (job_id,)).fetchone()

        if result:
            return Application.from_db_row(result)
        return None

    def update_application_status(self, application_id: str, status: str) -> None:
        """
        Update application status.

        Args:
            application_id: The application ID to update
            status: New status value
        """
        query = """
            UPDATE application_tracking
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
        """

        try:
            self.conn.execute(query, (status, application_id))
            logger.debug(f"Updated application {application_id} status to {status}")
        except Exception as e:
            logger.error(f"Failed to update application status: {e}")
            raise

    def update_application_stage(self, application_id: str, stage_name: str, stage_output: dict) -> None:
        """
        Update application stage information.

        Args:
            application_id: The application ID to update
            stage_name: Name of the current stage/agent
            stage_output: Output data from the stage
        """
        # First, get current application to update arrays
        app = self.get_application_by_id(application_id)
        if not app:
            logger.warning(f"Application {application_id} not found for stage update")
            return

        # Update the application object
        app.add_completed_stage(stage_name, stage_output)

        # Update in database
        query = """
            UPDATE application_tracking
            SET current_stage = ?,
                completed_stages = ?,
                stage_outputs = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
        """

        import json

        params = (stage_name, json.dumps(app.completed_stages), json.dumps(app.stage_outputs), application_id)

        try:
            self.conn.execute(query, params)
            logger.debug(f"Updated application {application_id} stage to {stage_name}")
        except Exception as e:
            logger.error(f"Failed to update application stage: {e}")
            raise

    def update_application_error(self, application_id: str, stage: str, error_type: str, error_message: str) -> None:
        """
        Record error information for a failed application.

        Args:
            application_id: The application ID to update
            stage: Stage where error occurred
            error_type: Type of error
            error_message: Error message
        """
        # Get current application
        app = self.get_application_by_id(application_id)
        if not app:
            logger.warning(f"Application {application_id} not found for error update")
            return

        # Set error using the model method
        app.set_error(stage, error_type, error_message)

        # Update in database
        query = """
            UPDATE application_tracking
            SET status = 'failed',
                error_info = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
        """

        import json

        params = (json.dumps(app.error_info), application_id)

        try:
            self.conn.execute(query, params)
            logger.debug(f"Recorded error for application {application_id}")
        except Exception as e:
            logger.error(f"Failed to update application error: {e}")
            raise

    def update_document_paths(self, application_id: str, cv_path: str | None = None, cl_path: str | None = None) -> None:
        """
        Update document file paths for an application.

        Args:
            application_id: The application ID to update
            cv_path: Path to CV file
            cl_path: Path to cover letter file
        """
        updates = []
        params = []

        if cv_path is not None:
            updates.append("cv_file_path = ?")
            params.append(cv_path)

        if cl_path is not None:
            updates.append("cl_file_path = ?")
            params.append(cl_path)

        if not updates:
            return

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(application_id)

        query = f"UPDATE application_tracking SET {', '.join(updates)} WHERE application_id = ?"

        try:
            self.conn.execute(query, params)
            logger.debug(f"Updated document paths for application {application_id}")
        except Exception as e:
            logger.error(f"Failed to update document paths: {e}")
            raise

    def update_submission_method(self, application_id: str, submission_method: str) -> None:
        """
        Update submission method for an application.

        Args:
            application_id: The application ID to update
            submission_method: Submission method (email, web_form, etc.)
        """
        query = """
            UPDATE application_tracking
            SET submission_method = ?, updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
        """

        try:
            self.conn.execute(query, (submission_method, application_id))
            logger.debug(f"Updated submission_method to {submission_method} for {application_id}")
        except Exception as e:
            logger.error(f"Failed to update submission method: {e}")
            raise

    def update_application_url(self, application_id: str, application_url: str) -> None:
        """
        Update application URL for an application.

        Note: This requires adding an application_url column to the database.
        For now, this is stored in stage_outputs.

        Args:
            application_id: The application ID to update
            application_url: URL for application submission
        """
        # Get current application to update stage_outputs
        app = self.get_application_by_id(application_id)
        if not app:
            logger.warning(f"Application {application_id} not found for URL update")
            return

        # Store in stage_outputs for now
        if "application_form_handler" not in app.stage_outputs:
            app.stage_outputs["application_form_handler"] = {}

        app.stage_outputs["application_form_handler"]["application_url"] = application_url

        # Update in database
        query = """
            UPDATE application_tracking
            SET stage_outputs = ?, updated_at = CURRENT_TIMESTAMP
            WHERE application_id = ?
        """

        import json

        try:
            self.conn.execute(query, (json.dumps(app.stage_outputs), application_id))
            logger.debug(f"Updated application_url for {application_id}")
        except Exception as e:
            logger.error(f"Failed to update application URL: {e}")
            raise

    def list_applications(self, filters: dict | None = None, limit: int = 100, offset: int = 0) -> list[Application]:
        """
        List applications with optional filtering and pagination.

        Args:
            filters: Dictionary of field filters (e.g., {"status": "matched"})
            limit: Maximum number of applications to return
            offset: Number of applications to skip (for pagination)

        Returns:
            List of Application instances
        """
        query = "SELECT * FROM application_tracking"
        params = []

        # Add WHERE clause if filters provided
        if filters:
            where_clauses = []
            for field, value in filters.items():
                where_clauses.append(f"{field} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(where_clauses)

        # Add ORDER BY for consistent pagination
        query += " ORDER BY created_at DESC"

        # Add LIMIT and OFFSET
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        results = self.conn.execute(query, params).fetchall()
        return [Application.from_db_row(row) for row in results]

    def count_applications(self, filters: dict | None = None) -> int:
        """
        Count applications with optional filtering.

        Args:
            filters: Dictionary of field filters

        Returns:
            Number of applications matching filters
        """
        query = "SELECT COUNT(*) FROM application_tracking"
        params = []

        if filters:
            where_clauses = []
            for field, value in filters.items():
                where_clauses.append(f"{field} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(where_clauses)

        result = self.conn.execute(query, params).fetchone()
        return result[0] if result else 0

    def get_application_history(
        self,
        platforms: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        min_score: int | None = None,
        max_score: int | None = None,
        statuses: list[str] | None = None,
        sort_by: str = "applied_date",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[dict], int]:
        """
        Get application history with filtering, sorting, and pagination.

        Args:
            platforms: List of platforms to filter by (linkedin, seek, indeed)
            date_from: Start date for filtering (ISO format YYYY-MM-DD)
            date_to: End date for filtering (ISO format YYYY-MM-DD)
            min_score: Minimum match score (0-100)
            max_score: Maximum match score (0-100)
            statuses: List of statuses to filter by
            sort_by: Column to sort by (title, company, platform, applied_date, match_score, status)
            sort_order: Sort order (asc or desc)
            page: Page number (starts at 1)
            page_size: Items per page

        Returns:
            Tuple of (list of application dicts, total count)
        """

        # Map frontend sort columns to SQL columns
        sort_column_map = {"title": "j.job_title", "company": "j.company_name", "platform": "j.platform_source", "applied_date": "a.submitted_timestamp", "match_score": "match_score", "status": "a.status"}

        # Build WHERE clauses
        where_clauses = []
        params = []

        # Filter by platforms
        if platforms:
            placeholders = ",".join(["?" for _ in platforms])
            where_clauses.append(f"j.platform_source IN ({placeholders})")
            params.extend(platforms)

        # Filter by date range
        if date_from:
            where_clauses.append("DATE(a.submitted_timestamp) >= ?")
            params.append(date_from)
        if date_to:
            where_clauses.append("DATE(a.submitted_timestamp) <= ?")
            params.append(date_to)

        # Filter by match score range
        if min_score is not None:
            where_clauses.append("CAST(json_extract(a.stage_outputs, '$.job_matcher.match_score') AS INTEGER) >= ?")
            params.append(min_score)
        if max_score is not None:
            where_clauses.append("CAST(json_extract(a.stage_outputs, '$.job_matcher.match_score') AS INTEGER) <= ?")
            params.append(max_score)

        # Filter by statuses
        if statuses:
            placeholders = ",".join(["?" for _ in statuses])
            where_clauses.append(f"a.status IN ({placeholders})")
            params.extend(statuses)

        # Build WHERE clause
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Get total count
        count_query = f"""
            SELECT COUNT(*)
            FROM application_tracking a
            JOIN jobs j ON a.job_id = j.job_id
            {where_sql}
        """
        count_result = self.conn.execute(count_query, params).fetchone()
        total = count_result[0] if count_result else 0

        # Build main query
        sort_column = sort_column_map.get(sort_by, "a.submitted_timestamp")
        sort_direction = "ASC" if sort_order == "asc" else "DESC"

        # Calculate offset
        offset = (page - 1) * page_size

        query = f"""
            SELECT
                a.application_id,
                j.job_title,
                j.company_name,
                j.platform_source as platform,
                a.submitted_timestamp as applied_date,
                CAST(json_extract(a.stage_outputs, '$.job_matcher.match_score') AS INTEGER) as match_score,
                a.status,
                a.cv_file_path,
                a.cl_file_path,
                j.job_url,
                j.location,
                j.salary_aud_per_day,
                j.job_description
            FROM application_tracking a
            JOIN jobs j ON a.job_id = j.job_id
            {where_sql}
            ORDER BY {sort_column} {sort_direction}
            LIMIT ? OFFSET ?
        """

        # Add pagination params
        query_params = params + [page_size, offset]

        results = self.conn.execute(query, query_params).fetchall()

        # Convert to list of dicts
        applications = []
        for row in results:
            applications.append(
                {
                    "application_id": row[0],
                    "job_title": row[1],
                    "company_name": row[2],
                    "platform": row[3],
                    "applied_date": row[4].isoformat() if row[4] else None,
                    "match_score": row[5] if row[5] is not None else 0,
                    "status": row[6],
                    "cv_file_path": row[7],
                    "cl_file_path": row[8],
                    "job_url": row[9],
                    "location": row[10],
                    "salary_aud_per_day": float(row[11]) if row[11] else None,
                    "job_description": row[12],
                }
            )

        return applications, total
