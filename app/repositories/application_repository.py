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

    def update_application_stage(
        self, application_id: str, stage_name: str, stage_output: dict
    ) -> None:
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

        params = (
            stage_name,
            json.dumps(app.completed_stages),
            json.dumps(app.stage_outputs),
            application_id,
        )

        try:
            self.conn.execute(query, params)
            logger.debug(f"Updated application {application_id} stage to {stage_name}")
        except Exception as e:
            logger.error(f"Failed to update application stage: {e}")
            raise

    def update_application_error(
        self, application_id: str, stage: str, error_type: str, error_message: str
    ) -> None:
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

    def update_document_paths(
        self, application_id: str, cv_path: str | None = None, cl_path: str | None = None
    ) -> None:
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

    def list_applications(
        self,
        filters: dict | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Application]:
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
