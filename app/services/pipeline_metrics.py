"""
Pipeline Metrics Service for Gradio UI.

Provides real-time metrics about jobs flowing through the agent pipeline,
agent execution statistics, and bottleneck identification.
"""

from typing import Any

from loguru import logger


class PipelineMetricsService:
    """
    Service for calculating pipeline metrics and agent execution statistics.

    Provides metrics such as:
    - Active jobs in pipeline
    - Agent execution times and success rates
    - Pipeline stage bottlenecks
    - Stage-wise job counts
    """

    # Agent stage name mapping
    AGENT_STAGE_NAMES = {
        "job_matcher": "Job Matcher",
        "salary_validator": "Salary Validator",
        "cv_tailor": "CV Tailor",
        "cover_letter_writer": "CL Writer",
        "qa_agent": "QA Agent",
        "orchestrator": "Orchestrator",
        "application_form_handler": "Form Handler",
    }

    # Status color mapping for UI
    STATUS_COLORS = {"completed": "green", "matched": "yellow", "sending": "yellow", "failed": "red", "pending": "blue", "discovered": "gray"}

    def __init__(self, db_connection: Any):
        """
        Initialize Pipeline Metrics Service.

        Args:
            db_connection: DuckDB database connection
        """
        self._db = db_connection
        logger.debug("[pipeline_metrics] Service initialized")

    def get_active_jobs_in_pipeline(self) -> list[dict[str, Any]]:
        """
        Get jobs currently active in the pipeline.

        Returns jobs that are not completed, rejected, or marked as duplicates.

        Returns:
            List of active jobs with details
        """
        try:
            query = """
                SELECT
                    at.job_id,
                    j.job_title,
                    j.company_name,
                    at.current_stage,
                    at.status,
                    at.updated_at,
                    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - at.updated_at))::INTEGER as seconds_in_stage
                FROM application_tracking at
                LEFT JOIN jobs j ON at.job_id = j.job_id
                WHERE at.status NOT IN ('completed', 'rejected', 'duplicate')
                ORDER BY at.updated_at DESC
                LIMIT 20
            """
            result = self._db.execute(query)
            rows = result.fetchall()

            jobs = []
            for row in rows:
                jobs.append({"job_id": row[0], "job_title": row[1], "company_name": row[2], "current_stage": row[3], "status": row[4], "updated_at": row[5], "time_in_stage": self.format_time_in_stage(row[6] if row[6] else 0)})

            logger.debug(f"[pipeline_metrics] Active jobs in pipeline: {len(jobs)}")
            return jobs

        except Exception as e:
            logger.error(f"[pipeline_metrics] Error getting active jobs: {e}")
            return []

    def get_agent_execution_metrics(self) -> dict[str, dict[str, Any]]:
        """
        Get execution metrics for each agent.

        Calculates average execution time, total executions, and success rate
        for each agent in the pipeline.

        Returns:
            Dictionary mapping agent name to metrics
        """
        try:
            query = """
                SELECT
                    current_stage as agent_name,
                    AVG(CASE
                        WHEN json_extract(stage_outputs, '$.execution_time') IS NOT NULL
                        THEN CAST(json_extract(stage_outputs, '$.execution_time') AS DOUBLE)
                        ELSE 0
                    END) as avg_execution_time,
                    COUNT(*) as total_executions,
                    (SUM(CASE WHEN status IN ('completed', 'matched', 'documents_generated', 'ready_to_send', 'sending') THEN 1 ELSE 0 END)::DOUBLE / COUNT(*) * 100) as success_rate
                FROM application_tracking
                WHERE current_stage IS NOT NULL
                GROUP BY current_stage
            """
            result = self._db.execute(query)
            rows = result.fetchall()

            metrics = {}
            for row in rows:
                agent_name = row[0]
                metrics[agent_name] = {"avg_execution_time": round(row[1], 2) if row[1] else 0.0, "total_executions": row[2], "success_rate": round(row[3], 1) if row[3] else 0.0}

            logger.debug(f"[pipeline_metrics] Agent metrics calculated for {len(metrics)} agents")
            return metrics

        except Exception as e:
            logger.error(f"[pipeline_metrics] Error getting agent metrics: {e}")
            return {}

    def get_stage_bottlenecks(self) -> list[dict[str, Any]]:
        """
        Identify pipeline stage bottlenecks.

        Returns stages with high job counts and long wait times,
        ordered by job count descending.

        Returns:
            List of bottleneck stages with details
        """
        try:
            query = """
                SELECT
                    current_stage,
                    COUNT(*) as job_count,
                    AVG(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - updated_at)))::INTEGER as avg_wait_time_sec
                FROM application_tracking
                WHERE status NOT IN ('completed', 'rejected', 'duplicate')
                    AND current_stage IS NOT NULL
                GROUP BY current_stage
                ORDER BY job_count DESC
            """
            result = self._db.execute(query)
            rows = result.fetchall()

            bottlenecks = []
            for row in rows:
                bottlenecks.append({"stage": row[0], "job_count": row[1], "avg_wait_time": self.format_time_in_stage(row[2] if row[2] else 0)})

            logger.debug(f"[pipeline_metrics] Identified {len(bottlenecks)} stage bottlenecks")
            return bottlenecks

        except Exception as e:
            logger.error(f"[pipeline_metrics] Error getting stage bottlenecks: {e}")
            return []

    def get_pipeline_stage_counts(self) -> dict[str, int]:
        """
        Get count of jobs at each pipeline stage.

        Returns:
            Dictionary mapping stage status to count
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

            counts = {row[0]: row[1] for row in rows} if rows else {}

            logger.debug(f"[pipeline_metrics] Stage counts: {counts}")
            return counts

        except Exception as e:
            logger.error(f"[pipeline_metrics] Error getting stage counts: {e}")
            return {}

    def format_time_in_stage(self, seconds: int) -> str:
        """
        Format time duration in human-readable format.

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted time string (e.g., "5m 30s" or "2h 15m")
        """
        # Convert to int to handle float inputs
        seconds = int(seconds)

        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    def get_all_pipeline_metrics(self) -> dict[str, Any]:
        """
        Get all pipeline metrics in one call.

        Returns:
            Dictionary containing all pipeline metrics
        """
        try:
            metrics = {"active_jobs": self.get_active_jobs_in_pipeline(), "agent_metrics": self.get_agent_execution_metrics(), "bottlenecks": self.get_stage_bottlenecks(), "stage_counts": self.get_pipeline_stage_counts()}

            logger.debug("[pipeline_metrics] Retrieved all pipeline metrics")
            return metrics

        except Exception as e:
            logger.error(f"[pipeline_metrics] Error getting all pipeline metrics: {e}")
            return {"active_jobs": [], "agent_metrics": {}, "bottlenecks": [], "stage_counts": {}}
