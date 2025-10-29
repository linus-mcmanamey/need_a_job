"""
Approval Mode Service.

Manages approval mode settings, pending approvals view, and approve/reject actions
for jobs awaiting manual approval before submission.
"""

import json
from datetime import datetime
from typing import Any

from loguru import logger


class ApprovalModeService:
    """Service for managing approval mode and pending approvals."""

    def __init__(self, db_connection: Any):
        """
        Initialize the approval mode service.

        Args:
            db_connection: Database connection instance
        """
        self._db = db_connection
        self._ensure_system_config_table()
        logger.debug("[approval_mode] Service initialized")

    def _ensure_system_config_table(self) -> None:
        """Ensure system_config table exists."""
        try:
            self._db.execute("""
                CREATE TABLE IF NOT EXISTS system_config (
                    config_key VARCHAR PRIMARY KEY,
                    config_value VARCHAR NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            logger.debug("[approval_mode] system_config table ensured")
        except Exception as e:
            logger.error(f"[approval_mode] Error creating system_config table: {e}")

    def get_approval_mode_enabled(self) -> bool:
        """
        Get current approval mode setting.

        Returns:
            bool: True if approval mode enabled, False otherwise
        """
        try:
            query = """
                SELECT config_value
                FROM system_config
                WHERE config_key = 'approval_mode_enabled'
            """
            result = self._db.execute(query)
            row = result.fetchone()

            if row:
                enabled = row[0].lower() == "true"
                logger.debug(f"[approval_mode] Approval mode enabled: {enabled}")
                return enabled

            logger.debug("[approval_mode] Approval mode not set, defaulting to false")
            return False

        except Exception as e:
            logger.error(f"[approval_mode] Error getting approval mode: {e}")
            return False

    def set_approval_mode(self, enabled: bool) -> bool:
        """
        Set approval mode enabled/disabled.

        Args:
            enabled: True to enable approval mode, False to disable

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            value = "true" if enabled else "false"
            query = """
                INSERT INTO system_config (config_key, config_value, updated_at)
                VALUES ('approval_mode_enabled', ?, CURRENT_TIMESTAMP)
                ON CONFLICT (config_key) DO UPDATE
                    SET config_value = ?, updated_at = CURRENT_TIMESTAMP
            """
            self._db.execute(query, (value, value))
            self._db.commit()

            logger.info(f"[approval_mode] Approval mode set to: {enabled}")
            return True

        except Exception as e:
            logger.error(f"[approval_mode] Error setting approval mode: {e}")
            return False

    def get_pending_approvals(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        Get list of jobs pending approval.

        Args:
            limit: Maximum number of jobs to return (default: 20)

        Returns:
            list[dict]: List of jobs with status="ready_to_send"
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
                WHERE at.status = 'ready_to_send'
                ORDER BY at.created_at ASC
                LIMIT ?
            """
            result = self._db.execute(query, (limit,))
            rows = result.fetchall()

            jobs = []
            for row in rows:
                job_record = {"job_id": row[0], "job_title": row[1], "company_name": row[2], "platform": row[3], "match_score": row[4], "cv_path": row[5], "cl_path": row[6], "created_at": row[7], "updated_at": row[8]}
                jobs.append(job_record)

            logger.debug(f"[approval_mode] Retrieved {len(jobs)} pending approvals")
            return jobs

        except Exception as e:
            logger.error(f"[approval_mode] Error getting pending approvals: {e}")
            return []

    def get_approval_summary(self) -> dict[str, Any]:
        """
        Get summary metrics for approval mode.

        Returns:
            dict: Summary with pending_count, avg_match_score, oldest_job_days, approval_mode_enabled
        """
        try:
            # Get approval mode status
            approval_enabled = self.get_approval_mode_enabled()

            # Get summary metrics
            query = """
                SELECT
                    COUNT(*) as pending_count,
                    AVG(match_score) as avg_match_score,
                    MIN(created_at) as oldest_job_date
                FROM application_tracking
                WHERE status = 'ready_to_send'
            """
            result = self._db.execute(query)
            row = result.fetchone()

            pending_count = row[0] if row else 0
            avg_match_score = row[1] if row and row[1] else 0.0
            oldest_job_date = row[2] if row and row[2] else None

            # Calculate days since oldest job
            oldest_job_days = 0
            if oldest_job_date:
                days_diff = (datetime.now() - oldest_job_date).days
                oldest_job_days = max(0, days_diff)

            summary = {"pending_count": pending_count, "avg_match_score": round(avg_match_score, 2) if avg_match_score else 0.0, "oldest_job_days": oldest_job_days, "approval_mode_enabled": approval_enabled}

            logger.debug(f"[approval_mode] Summary: {summary}")
            return summary

        except Exception as e:
            logger.error(f"[approval_mode] Error getting approval summary: {e}")
            return {"pending_count": 0, "avg_match_score": 0.0, "oldest_job_days": 0, "approval_mode_enabled": False}

    def approve_job(self, job_id: str) -> dict[str, Any]:
        """
        Approve a job for submission.

        Args:
            job_id: Job ID to approve

        Returns:
            dict: Response with success, message, job_id
        """
        try:
            query = """
                UPDATE application_tracking
                SET
                    status = 'approved',
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """
            result = self._db.execute(query, (job_id,))
            self._db.commit()

            if result.rowcount > 0:
                logger.info(f"[approval_mode] Job {job_id} approved")
                return {"success": True, "message": "Job approved and ready for submission", "job_id": job_id}
            else:
                logger.warning(f"[approval_mode] Job {job_id} not found for approval")
                return {"success": False, "message": "Job not found", "job_id": job_id}

        except Exception as e:
            logger.error(f"[approval_mode] Error approving job {job_id}: {e}")
            return {"success": False, "message": f"Error: {e!s}", "job_id": job_id}

    def reject_job(self, job_id: str, reason: str) -> dict[str, Any]:
        """
        Reject a job from submission.

        Args:
            job_id: Job ID to reject
            reason: Rejection reason

        Returns:
            dict: Response with success, message, job_id
        """
        try:
            rejection_info = json.dumps({"rejection_reason": reason, "rejection_timestamp": datetime.now().isoformat(), "manual_action": "reject"})

            query = """
                UPDATE application_tracking
                SET
                    status = 'rejected',
                    error_info = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE job_id = ?
            """
            result = self._db.execute(query, (rejection_info, job_id))
            self._db.commit()

            if result.rowcount > 0:
                logger.info(f"[approval_mode] Job {job_id} rejected: {reason}")
                return {"success": True, "message": "Job rejected", "job_id": job_id}
            else:
                logger.warning(f"[approval_mode] Job {job_id} not found for rejection")
                return {"success": False, "message": "Job not found", "job_id": job_id}

        except Exception as e:
            logger.error(f"[approval_mode] Error rejecting job {job_id}: {e}")
            return {"success": False, "message": f"Error: {e!s}", "job_id": job_id}
