"""
Dashboard Metrics Service for Gradio UI.

Provides aggregated metrics and statistics about job discovery and application pipeline.
"""

from typing import Any

from loguru import logger


class DashboardMetricsService:
    """
    Service for calculating dashboard metrics from the database.

    Provides metrics such as:
    - Jobs discovered today
    - Applications sent (today and all time)
    - Pending jobs count
    - Success rate
    - Status breakdown
    - Recent activity feed
    """

    def __init__(self, db_connection: Any):
        """
        Initialize Dashboard Metrics Service.

        Args:
            db_connection: DuckDB database connection
        """
        self._db = db_connection
        logger.debug("[dashboard_metrics] Service initialized")

    def get_jobs_discovered_today(self) -> int:
        """
        Get count of jobs discovered today.

        Returns:
            Number of jobs added today
        """
        try:
            query = """
                SELECT COUNT(*) as count
                FROM jobs
                WHERE DATE(discovered_timestamp) = CURRENT_DATE
            """
            result = self._db.execute(query)
            row = result.fetchone()
            count = row[0] if row else 0

            logger.debug(f"[dashboard_metrics] Jobs discovered today: {count}")
            return count

        except Exception as e:
            logger.error(f"[dashboard_metrics] Error getting jobs discovered today: {e}")
            return 0

    def get_applications_sent(self, period: str = "all") -> int:
        """
        Get count of applications sent.

        Args:
            period: Time period - "all" or "today"

        Returns:
            Number of completed applications
        """
        try:
            if period == "today":
                query = """
                    SELECT COUNT(*) as count
                    FROM application_tracking
                    WHERE status = 'completed'
                    AND DATE(submitted_timestamp) = CURRENT_DATE
                """
            else:
                query = """
                    SELECT COUNT(*) as count
                    FROM application_tracking
                    WHERE status = 'completed'
                """

            result = self._db.execute(query)
            row = result.fetchone()
            count = row[0] if row else 0

            logger.debug(f"[dashboard_metrics] Applications sent ({period}): {count}")
            return count

        except Exception as e:
            logger.error(f"[dashboard_metrics] Error getting applications sent: {e}")
            return 0

    def get_pending_count(self) -> int:
        """
        Get count of jobs requiring manual intervention.

        Returns:
            Number of pending or failed jobs
        """
        try:
            query = """
                SELECT COUNT(*) as count
                FROM application_tracking
                WHERE status IN ('pending', 'failed')
            """
            result = self._db.execute(query)
            row = result.fetchone()
            count = row[0] if row else 0

            logger.debug(f"[dashboard_metrics] Pending jobs: {count}")
            return count

        except Exception as e:
            logger.error(f"[dashboard_metrics] Error getting pending count: {e}")
            return 0

    def get_success_rate(self) -> float:
        """
        Calculate success rate (completed / total discovered).

        Returns:
            Success rate as percentage (0-100)
        """
        try:
            # Get total jobs discovered
            total_query = "SELECT COUNT(*) FROM jobs"
            total_result = self._db.execute(total_query)
            total_row = total_result.fetchone()
            total = total_row[0] if total_row else 0

            if total == 0:
                return 0.0

            # Get completed applications
            completed_query = """
                SELECT COUNT(*) FROM application_tracking
                WHERE status = 'completed'
            """
            completed_result = self._db.execute(completed_query)
            completed_row = completed_result.fetchone()
            completed = completed_row[0] if completed_row else 0

            rate = (completed / total) * 100 if total > 0 else 0.0

            logger.debug(f"[dashboard_metrics] Success rate: {rate:.1f}% ({completed}/{total})")
            return round(rate, 1)

        except Exception as e:
            logger.error(f"[dashboard_metrics] Error calculating success rate: {e}")
            return 0.0

    def get_status_breakdown(self) -> dict[str, int]:
        """
        Get breakdown of jobs by status.

        Returns:
            Dictionary mapping status to count
        """
        try:
            query = """
                SELECT status, COUNT(*) as count
                FROM application_tracking
                GROUP BY status
                ORDER BY count DESC
            """
            result = self._db.execute(query)
            rows = result.fetchall()

            breakdown = {row[0]: row[1] for row in rows} if rows else {}

            logger.debug(f"[dashboard_metrics] Status breakdown: {breakdown}")
            return breakdown

        except Exception as e:
            logger.error(f"[dashboard_metrics] Error getting status breakdown: {e}")
            return {}

    def get_recent_activity(self, limit: int = 10) -> list[dict[str, Any]]:
        """
        Get recent job activity.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of recent jobs with details
        """
        try:
            query = """
                SELECT
                    j.job_id,
                    j.job_title,
                    j.company_name,
                    at.status,
                    at.updated_at
                FROM jobs j
                LEFT JOIN application_tracking at ON j.job_id = at.job_id
                ORDER BY at.updated_at DESC
                LIMIT ?
            """
            result = self._db.execute(query, (limit,))
            rows = result.fetchall()

            activity = []
            for row in rows:
                activity.append({"job_id": row[0], "job_title": row[1], "company_name": row[2], "status": row[3], "updated_at": row[4]})

            logger.debug(f"[dashboard_metrics] Recent activity: {len(activity)} jobs")
            return activity

        except Exception as e:
            logger.error(f"[dashboard_metrics] Error getting recent activity: {e}")
            return []

    def get_all_metrics(self) -> dict[str, Any]:
        """
        Get all dashboard metrics in one call.

        Returns:
            Dictionary containing all metrics
        """
        try:
            metrics = {
                "jobs_discovered_today": self.get_jobs_discovered_today(),
                "applications_sent_all": self.get_applications_sent(period="all"),
                "applications_sent_today": self.get_applications_sent(period="today"),
                "pending_count": self.get_pending_count(),
                "success_rate": self.get_success_rate(),
                "status_breakdown": self.get_status_breakdown(),
                "recent_activity": self.get_recent_activity(),
            }

            logger.debug("[dashboard_metrics] Retrieved all metrics")
            return metrics

        except Exception as e:
            logger.error(f"[dashboard_metrics] Error getting all metrics: {e}")
            return {"jobs_discovered_today": 0, "applications_sent_all": 0, "applications_sent_today": 0, "pending_count": 0, "success_rate": 0.0, "status_breakdown": {}, "recent_activity": []}
