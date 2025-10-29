"""
Pending Jobs Service for Gradio UI.

Provides management functionality for jobs requiring manual intervention,
including error details, retry operations, and status updates.
"""

import json
from datetime import datetime
from typing import Any

from loguru import logger


class PendingJobsService:
    """
    Service for managing pending and failed jobs.

    Provides functionality for:
    - Retrieving jobs requiring manual intervention
    - Error summary aggregation
    - Retry operations
    - Skip/reject operations
    - Manual completion marking
    - Job details retrieval
    """

    def __init__(self, db_connection: Any):
        """
        Initialize Pending Jobs Service.

        Args:
            db_connection: DuckDB database connection
        """
        self._db = db_connection
        logger.debug("[pending_jobs] Service initialized")

    def get_pending_jobs(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get list of jobs requiring manual intervention.

        Returns jobs with status='pending' or status='failed', ordered by
        most recent first.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of pending jobs with error details
        """
        try:
            query = """
                SELECT
                    at.job_id,
                    j.job_title,
                    j.company_name,
                    j.platform_source,
                    at.status,
                    at.current_stage,
                    at.error_info,
                    at.updated_at
                FROM application_tracking at
                LEFT JOIN jobs j ON at.job_id = j.job_id
                WHERE at.status IN ('pending', 'failed')
                ORDER BY at.updated_at DESC
                LIMIT ?
            """
            result = self._db.execute(query, (limit,))
            rows = result.fetchall()

            jobs = []
            for row in rows:
                # Parse error_info JSON
                error_type = "unknown"
                error_message = "Error info unavailable"

                if row[6]:  # error_info field
                    try:
                        error_data = json.loads(row[6])
                        error_type = error_data.get("error_type", "unknown")
                        error_message = error_data.get("error_message", "No error message")
                    except (json.JSONDecodeError, TypeError):
                        pass  # Use defaults

                job_record = {"job_id": row[0], "job_title": row[1], "company_name": row[2], "platform": row[3], "status": row[4], "failed_stage": row[5], "error_type": error_type, "error_message": error_message, "updated_at": row[7]}
                jobs.append(job_record)

            logger.debug(f"[pending_jobs] Retrieved {len(jobs)} pending jobs")
            return jobs

        except Exception as e:
            logger.error(f"[pending_jobs] Error getting pending jobs: {e}")
            return []

    def get_error_summary(self) -> dict[str, int]:
        """
        Get summary of errors by type.

        Aggregates error counts from pending/failed jobs.

        Returns:
            Dictionary mapping error type to count
        """
        try:
            query = """
                SELECT
                    json_extract(error_info, '$.error_type') as error_type,
                    COUNT(*) as count
                FROM application_tracking
                WHERE status IN ('pending', 'failed')
                    AND error_info IS NOT NULL
                GROUP BY error_type
                ORDER BY count DESC
            """
            result = self._db.execute(query)
            rows = result.fetchall()

            summary = {row[0]: row[1] for row in rows if row[0]} if rows else {}

            logger.debug(f"[pending_jobs] Error summary: {summary}")
            return summary

        except Exception as e:
            logger.error(f"[pending_jobs] Error getting error summary: {e}")
            return {}

    def retry_job(self, job_id: str) -> dict[str, Any]:
        """
        Retry a failed job by clearing error info and resetting status.

        Args:
            job_id: ID of job to retry

        Returns:
            Result dictionary with success status and message
        """
        try:
            query = """
                UPDATE application_tracking
                SET
                    error_info = NULL,
                    status = 'matched',
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """
            result = self._db.execute(query, (job_id,))
            self._db.commit()

            if result.rowcount > 0:
                logger.info(f"[pending_jobs] Job {job_id} queued for retry")
                return {"success": True, "message": "Job queued for retry", "job_id": job_id}
            else:
                logger.warning(f"[pending_jobs] Job {job_id} not found for retry")
                return {"success": False, "message": "Job not found", "job_id": job_id}

        except Exception as e:
            logger.error(f"[pending_jobs] Error retrying job {job_id}: {e}")
            return {"success": False, "message": f"Error: {e!s}", "job_id": job_id}

    def skip_job(self, job_id: str, reason: str) -> dict[str, Any]:
        """
        Skip a job by marking it as rejected.

        Args:
            job_id: ID of job to skip
            reason: Reason for skipping

        Returns:
            Result dictionary with success status and message
        """
        try:
            skip_info = json.dumps({"skip_reason": reason, "skip_timestamp": datetime.now().isoformat(), "manual_action": "skip"})

            query = """
                UPDATE application_tracking
                SET
                    status = 'rejected',
                    error_info = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """
            result = self._db.execute(query, (skip_info, job_id))
            self._db.commit()

            if result.rowcount > 0:
                logger.info(f"[pending_jobs] Job {job_id} marked as rejected: {reason}")
                return {"success": True, "message": "Job marked as rejected", "job_id": job_id}
            else:
                logger.warning(f"[pending_jobs] Job {job_id} not found for skip")
                return {"success": False, "message": "Job not found", "job_id": job_id}

        except Exception as e:
            logger.error(f"[pending_jobs] Error skipping job {job_id}: {e}")
            return {"success": False, "message": f"Error: {e!s}", "job_id": job_id}

    def mark_manual_complete(self, job_id: str) -> dict[str, Any]:
        """
        Mark a job as manually completed outside the system.

        Args:
            job_id: ID of job to mark as complete

        Returns:
            Result dictionary with success status and message
        """
        try:
            completion_info = json.dumps({"manual_completion": True, "timestamp": datetime.now().isoformat(), "manual_action": "complete"})

            query = """
                UPDATE application_tracking
                SET
                    status = 'completed',
                    error_info = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """
            result = self._db.execute(query, (completion_info, job_id))
            self._db.commit()

            if result.rowcount > 0:
                logger.info(f"[pending_jobs] Job {job_id} marked as manually completed")
                return {"success": True, "message": "Job marked as manually completed", "job_id": job_id}
            else:
                logger.warning(f"[pending_jobs] Job {job_id} not found for manual complete")
                return {"success": False, "message": "Job not found", "job_id": job_id}

        except Exception as e:
            logger.error(f"[pending_jobs] Error marking job {job_id} as complete: {e}")
            return {"success": False, "message": f"Error: {e!s}", "job_id": job_id}

    def get_job_details(self, job_id: str) -> dict[str, Any]:
        """
        Get detailed information about a specific job.

        Args:
            job_id: ID of job to retrieve

        Returns:
            Dictionary with job details, or empty dict if not found
        """
        try:
            query = """
                SELECT
                    at.job_id,
                    j.job_title,
                    j.company_name,
                    j.platform_source,
                    j.job_url,
                    at.status,
                    at.current_stage,
                    at.error_info,
                    at.stage_outputs,
                    at.updated_at
                FROM application_tracking at
                LEFT JOIN jobs j ON at.job_id = j.job_id
                WHERE at.job_id = ?
            """
            result = self._db.execute(query, (job_id,))
            row = result.fetchone()

            if not row:
                return {}

            # Parse error_info JSON
            error_type = "unknown"
            error_message = "No error info"
            if row[7]:
                try:
                    error_data = json.loads(row[7])
                    error_type = error_data.get("error_type", "unknown")
                    error_message = error_data.get("error_message", "No error message")
                except (json.JSONDecodeError, TypeError):
                    pass

            # Parse stage_outputs JSON
            completed_stages = []
            if row[8]:
                try:
                    stage_data = json.loads(row[8])
                    completed_stages = list(stage_data.keys())
                except (json.JSONDecodeError, TypeError):
                    pass

            details = {
                "job_id": row[0],
                "job_title": row[1],
                "company_name": row[2],
                "platform": row[3],
                "job_url": row[4],
                "status": row[5],
                "current_stage": row[6],
                "error_type": error_type,
                "error_message": error_message,
                "completed_stages": completed_stages,
                "updated_at": row[9],
            }

            logger.debug(f"[pending_jobs] Retrieved details for job {job_id}")
            return details

        except Exception as e:
            logger.error(f"[pending_jobs] Error getting job details for {job_id}: {e}")
            return {}
