"""
Dry-Run Mode Service.

Manages dry-run mode settings, dry-run results view, and send now action
for jobs in dry-run testing state.
"""

from datetime import datetime
from typing import Any

from loguru import logger


class DryRunModeService:
    """Service for managing dry-run mode and dry-run results."""

    def __init__(self, db_connection: Any):
        """
        Initialize the dry-run mode service.

        Args:
            db_connection: Database connection instance
        """
        self._db = db_connection
        logger.debug("[dry_run_mode] Service initialized")

    def get_dry_run_mode_enabled(self) -> bool:
        """
        Get current dry-run mode setting.

        Returns:
            bool: True if dry-run mode enabled, False otherwise
        """
        try:
            query = """
                SELECT config_value
                FROM system_config
                WHERE config_key = 'dry_run_mode_enabled'
            """
            result = self._db.execute(query)
            row = result.fetchone()

            if row:
                enabled = row[0].lower() == "true"
                logger.debug(f"[dry_run_mode] Dry-run mode enabled: {enabled}")
                return enabled

            logger.debug("[dry_run_mode] Dry-run mode not set, defaulting to false")
            return False

        except Exception as e:
            logger.error(f"[dry_run_mode] Error getting dry-run mode: {e}")
            return False

    def set_dry_run_mode(self, enabled: bool) -> bool:
        """
        Set dry-run mode enabled/disabled.

        Args:
            enabled: True to enable dry-run mode, False to disable

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            value = "true" if enabled else "false"
            query = """
                INSERT INTO system_config (config_key, config_value, updated_at)
                VALUES ('dry_run_mode_enabled', ?, CURRENT_TIMESTAMP)
                ON CONFLICT (config_key) DO UPDATE
                    SET config_value = ?, updated_at = CURRENT_TIMESTAMP
            """
            self._db.execute(query, (value, value))
            self._db.commit()

            logger.info(f"[dry_run_mode] Dry-run mode set to: {enabled}")
            return True

        except Exception as e:
            logger.error(f"[dry_run_mode] Error setting dry-run mode: {e}")
            return False

    def get_dry_run_results(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get list of dry-run jobs.

        Args:
            limit: Maximum number of jobs to return (default: 20)

        Returns:
            list[dict]: List of jobs with status="dry_run_complete"
        """
        try:
            query = """
                SELECT
                    at.job_id,
                    j.job_title,
                    j.company_name,
                    j.platform_source,
                    at.match_score,
                    at.cv_file_path,
                    at.cl_file_path,
                    at.created_at,
                    at.updated_at
                FROM application_tracking at
                LEFT JOIN jobs j ON at.job_id = j.job_id
                WHERE at.status = 'dry_run_complete'
                ORDER BY at.created_at DESC
                LIMIT ?
            """
            result = self._db.execute(query, (limit,))
            rows = result.fetchall()

            jobs = []
            for row in rows:
                job_record = {"job_id": row[0], "job_title": row[1], "company_name": row[2], "platform": row[3], "match_score": row[4], "cv_path": row[5], "cl_path": row[6], "created_at": row[7], "updated_at": row[8]}
                jobs.append(job_record)

            logger.debug(f"[dry_run_mode] Retrieved {len(jobs)} dry-run results")
            return jobs

        except Exception as e:
            logger.error(f"[dry_run_mode] Error getting dry-run results: {e}")
            return []

    def get_dry_run_analytics(self) -> dict[str, Any]:
        """
        Get analytics metrics for dry-run mode.

        Returns:
            dict: Analytics with dry_run_count, avg_match_score, newest_job_hours, dry_run_mode_enabled
        """
        try:
            # Get dry-run mode status
            dry_run_enabled = self.get_dry_run_mode_enabled()

            # Get analytics metrics
            query = """
                SELECT
                    COUNT(*) as dry_run_count,
                    AVG(match_score) as avg_match_score,
                    MAX(created_at) as newest_job_date
                FROM application_tracking
                WHERE status = 'dry_run_complete'
            """
            result = self._db.execute(query)
            row = result.fetchone()

            dry_run_count = row[0] if row else 0
            avg_match_score = row[1] if row and row[1] else 0.0
            newest_job_date = row[2] if row and row[2] else None

            # Calculate hours since newest job
            newest_job_hours = 0
            if newest_job_date:
                hours_diff = (datetime.now() - newest_job_date).total_seconds() / 3600
                newest_job_hours = max(0, int(hours_diff))

            analytics = {"dry_run_count": dry_run_count, "avg_match_score": round(avg_match_score, 2) if avg_match_score else 0.0, "newest_job_hours": newest_job_hours, "dry_run_mode_enabled": dry_run_enabled}

            logger.debug(f"[dry_run_mode] Analytics: {analytics}")
            return analytics

        except Exception as e:
            logger.error(f"[dry_run_mode] Error getting dry-run analytics: {e}")
            return {"dry_run_count": 0, "avg_match_score": 0.0, "newest_job_hours": 0, "dry_run_mode_enabled": False}

    def send_now(self, job_id: str) -> dict[str, Any]:
        """
        Convert dry-run job to live (ready_to_send).

        Args:
            job_id: Job ID to send

        Returns:
            dict: Response with success, message, job_id
        """
        try:
            query = """
                UPDATE application_tracking
                SET
                    status = 'ready_to_send',
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
                    AND status = 'dry_run_complete'
            """
            result = self._db.execute(query, (job_id,))
            self._db.commit()

            if result.rowcount > 0:
                logger.info(f"[dry_run_mode] Job {job_id} moved to ready_to_send")
                return {"success": True, "message": "Job moved to ready_to_send", "job_id": job_id}
            else:
                logger.warning(f"[dry_run_mode] Job {job_id} not found or not in dry-run state")
                return {"success": False, "message": "Job not found or not in dry-run state", "job_id": job_id}

        except Exception as e:
            logger.error(f"[dry_run_mode] Error sending job {job_id}: {e}")
            return {"success": False, "message": f"Error: {e!s}", "job_id": job_id}
