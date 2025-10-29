"""
Gradio UI application for the Job Application Automation System.

This module provides a web-based user interface for monitoring and controlling
the automated job application system.
"""

import os
from typing import Any

import gradio as gr
from loguru import logger

from app.repositories.database import DatabaseConnection
from app.services.dashboard_metrics import DashboardMetricsService
from app.services.pipeline_metrics import PipelineMetricsService

# Global service instances
_metrics_service: DashboardMetricsService | None = None
_pipeline_service: PipelineMetricsService | None = None


def get_metrics_service() -> DashboardMetricsService:
    """Get or create metrics service instance."""
    global _metrics_service
    if _metrics_service is None:
        db = DatabaseConnection()
        _metrics_service = DashboardMetricsService(db.get_connection())
    return _metrics_service


def get_pipeline_service() -> PipelineMetricsService:
    """Get or create pipeline metrics service instance."""
    global _pipeline_service
    if _pipeline_service is None:
        db = DatabaseConnection()
        _pipeline_service = PipelineMetricsService(db.get_connection())
    return _pipeline_service


def load_dashboard_metrics() -> tuple[int, int, int, float, dict[str, Any], list[list[Any]]]:
    """
    Load all dashboard metrics from database.

    Returns:
        Tuple of (jobs_today, apps_sent, pending, success_rate, status_data, activity_data)
    """
    try:
        service = get_metrics_service()
        metrics = service.get_all_metrics()

        # Format status breakdown for bar plot
        status_data = {"status": list(metrics["status_breakdown"].keys()), "count": list(metrics["status_breakdown"].values())}

        # Format recent activity for dataframe
        activity_data = [
            [activity["updated_at"].strftime("%Y-%m-%d %H:%M") if activity.get("updated_at") else "N/A", activity.get("job_title", "N/A"), activity.get("company_name", "N/A"), activity.get("status", "N/A")]
            for activity in metrics["recent_activity"]
        ]

        return (metrics["jobs_discovered_today"], metrics["applications_sent_all"], metrics["pending_count"], metrics["success_rate"], status_data, activity_data)

    except Exception as e:
        logger.error(f"[gradio_app] Error loading dashboard metrics: {e}")
        return (0, 0, 0, 0.0, {"status": [], "count": []}, [])


def create_dashboard_tab() -> gr.Blocks:
    """
    Create the dashboard tab with metrics and status overview.

    Returns:
        Gradio Blocks component
    """
    with gr.Column() as dashboard:
        gr.Markdown("# 📊 Dashboard")
        gr.Markdown("Real-time metrics and system status")

        with gr.Row():
            jobs_today = gr.Number(label="Jobs Discovered Today", value=0, interactive=False)
            apps_sent = gr.Number(label="Applications Sent", value=0, interactive=False)
            pending = gr.Number(label="Pending Jobs", value=0, interactive=False)
            success_rate = gr.Number(label="Success Rate (%)", value=0.0, interactive=False)

        gr.Markdown("### Status Breakdown")
        status_chart = gr.BarPlot(value={"status": [], "count": []}, x="status", y="count", title="Jobs by Status", height=300)

        gr.Markdown("### Recent Activity")
        activity_table = gr.Dataframe(value=[], headers=["Time", "Job Title", "Company", "Status"], label="Last 10 Jobs")

        # Refresh button
        refresh_btn = gr.Button("🔄 Refresh Metrics", variant="secondary")

        # Auto-refresh timer (every 30 seconds)
        timer = gr.Timer(30)

        # Wire up refresh logic
        refresh_outputs = [jobs_today, apps_sent, pending, success_rate, status_chart, activity_table]

        refresh_btn.click(fn=load_dashboard_metrics, outputs=refresh_outputs)
        timer.tick(fn=load_dashboard_metrics, outputs=refresh_outputs)

        # Load initial data
        dashboard.load(fn=load_dashboard_metrics, outputs=refresh_outputs)

    return dashboard


def load_pipeline_metrics() -> tuple[list[list[Any]], dict[str, Any]]:
    """
    Load pipeline metrics from database.

    Returns:
        Tuple of (active_jobs_data, agent_performance_data)
    """
    try:
        service = get_pipeline_service()
        metrics = service.get_all_pipeline_metrics()

        # Format active jobs for dataframe
        active_jobs_data = [
            [job.get("job_id", "N/A"), job.get("job_title", "N/A"), job.get("company_name", "N/A"), job.get("current_stage", "N/A"), job.get("status", "N/A"), job.get("time_in_stage", "N/A")] for job in metrics["active_jobs"]
        ]

        # Format agent metrics for bar plot
        agent_names = []
        avg_times = []
        for agent_name, metrics_data in metrics["agent_metrics"].items():
            # Use friendly agent names
            friendly_name = service.AGENT_STAGE_NAMES.get(agent_name, agent_name)
            agent_names.append(friendly_name)
            avg_times.append(metrics_data.get("avg_execution_time", 0.0))

        agent_performance_data = {"agent": agent_names, "avg_time_sec": avg_times}

        logger.debug(f"[gradio_app] Pipeline metrics loaded: {len(active_jobs_data)} active jobs")
        return (active_jobs_data, agent_performance_data)

    except Exception as e:
        logger.error(f"[gradio_app] Error loading pipeline metrics: {e}")
        return ([], {"agent": [], "avg_time_sec": []})


def create_pipeline_tab() -> gr.Blocks:
    """
    Create the pipeline view tab showing real-time agent flow.

    Returns:
        Gradio Blocks component
    """
    with gr.Column() as pipeline:
        gr.Markdown("# 🔄 Job Pipeline")
        gr.Markdown("Watch jobs flow through the agent pipeline in real-time")

        active_jobs_table = gr.Dataframe(value=[], headers=["Job ID", "Title", "Company", "Current Stage", "Status", "Time in Stage"], label="Active Jobs in Pipeline")

        gr.Markdown("### Agent Performance")
        agent_performance_chart = gr.BarPlot(value={"agent": [], "avg_time_sec": []}, x="agent", y="avg_time_sec", title="Average Execution Time per Agent (seconds)", height=300)

        # Refresh button
        refresh_btn = gr.Button("🔄 Refresh Pipeline", variant="secondary")

        # Auto-refresh timer (every 30 seconds)
        timer = gr.Timer(30)

        # Wire up refresh logic
        refresh_outputs = [active_jobs_table, agent_performance_chart]

        refresh_btn.click(fn=load_pipeline_metrics, outputs=refresh_outputs)
        timer.tick(fn=load_pipeline_metrics, outputs=refresh_outputs)

        # Load initial data
        pipeline.load(fn=load_pipeline_metrics, outputs=refresh_outputs)

    return pipeline


def create_pending_tab() -> gr.Blocks:
    """
    Create the pending jobs management tab.

    Returns:
        Gradio Blocks component
    """
    with gr.Column() as pending:
        gr.Markdown("# ⏸️ Pending Jobs")
        gr.Markdown("Manage jobs requiring manual intervention")

        gr.Dataframe(value=[], headers=["Job ID", "Title", "Company", "Error Type", "Error Message", "Actions"], label="Pending Jobs")

        with gr.Row():
            gr.Button("Retry Selected", variant="primary")
            gr.Button("Skip Selected", variant="secondary")
            gr.Button("Mark as Manual Complete")

        gr.Markdown("### Error Summary")
        gr.BarPlot(value={"error_type": [], "count": []}, x="error_type", y="count", title="Errors by Type", height=250)

    return pending


def create_settings_tab() -> gr.Blocks:
    """
    Create the settings and control tab.

    Returns:
        Gradio Blocks component
    """
    with gr.Column() as settings:
        gr.Markdown("# ⚙️ Settings & Controls")

        gr.Markdown("### System Controls")
        with gr.Row():
            gr.Checkbox(label="Require approval before sending", value=True)
            gr.Checkbox(label="Dry-run mode (don't send applications)", value=False)

        gr.Markdown("### Discovery Settings")
        with gr.Row():
            gr.Checkbox(label="Enable automatic job discovery", value=False)
            gr.Slider(minimum=1, maximum=24, value=1, step=1, label="Discovery interval (hours)")

        gr.Markdown("### Matching Thresholds")
        with gr.Row():
            gr.Slider(minimum=0.0, maximum=1.0, value=0.70, step=0.05, label="Job match threshold")
            gr.Slider(minimum=0.0, maximum=1.0, value=0.90, step=0.05, label="Duplicate detection threshold")

        gr.Button("Save Settings", variant="primary")
        gr.Textbox(label="Status", value="", interactive=False)

    return settings


def create_ui() -> gr.Blocks:
    """
    Create the main Gradio UI application.

    Returns:
        Gradio Blocks interface
    """
    with gr.Blocks(title="Job Application Automation System", theme=gr.themes.Soft()) as app:
        gr.Markdown(
            """
            # 🤖 Job Application Automation System
            ### Automated Job Search and Application for Data Engineering Roles
            """
        )

        with gr.Tabs():
            with gr.Tab("Dashboard"):
                create_dashboard_tab()

            with gr.Tab("Pipeline"):
                create_pipeline_tab()

            with gr.Tab("Pending Jobs"):
                create_pending_tab()

            with gr.Tab("Settings"):
                create_settings_tab()

        gr.Markdown(
            """
            ---
            **Status:** MVP Phase 1 - Foundation
            **Version:** 1.0.0-mvp
            *Built with FastAPI, Gradio, DuckDB, and Claude AI*
            """
        )

    return app


def start(server_name: str = "0.0.0.0", server_port: int = 7860, share: bool = False) -> None:
    """
    Start the Gradio UI server.

    Args:
        server_name: Server host address
        server_port: Server port number
        share: Whether to create a public share link
    """
    try:
        logger.info(f"Starting Gradio UI on {server_name}:{server_port}")
        app = create_ui()
        app.launch(server_name=server_name, server_port=server_port, share=share, show_api=False)
    except Exception as e:
        logger.error(f"Failed to start Gradio UI: {e}")
        raise


if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv

    load_dotenv()

    # Configure logging
    logger.add("logs/gradio_app.log", rotation="1 day", retention="30 days", level="INFO")

    # Start the UI
    port = int(os.getenv("GRADIO_PORT", "7860"))
    start(server_port=port)
