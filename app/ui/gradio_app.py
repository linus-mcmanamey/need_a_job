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
from app.services.approval_mode import ApprovalModeService
from app.services.dashboard_metrics import DashboardMetricsService
from app.services.dry_run_mode import DryRunModeService
from app.services.pending_jobs import PendingJobsService
from app.services.pipeline_metrics import PipelineMetricsService

# Global service instances
_metrics_service: DashboardMetricsService | None = None
_pipeline_service: PipelineMetricsService | None = None
_pending_service: PendingJobsService | None = None
_approval_service: ApprovalModeService | None = None
_dry_run_service: DryRunModeService | None = None


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


def get_pending_service() -> PendingJobsService:
    """Get or create pending jobs service instance."""
    global _pending_service
    if _pending_service is None:
        db = DatabaseConnection()
        _pending_service = PendingJobsService(db.get_connection())
    return _pending_service


def get_approval_service() -> ApprovalModeService:
    """Get or create approval mode service instance."""
    global _approval_service
    if _approval_service is None:
        db = DatabaseConnection()
        _approval_service = ApprovalModeService(db.get_connection())
    return _approval_service


def get_dry_run_service() -> DryRunModeService:
    """Get or create dry-run mode service instance."""
    global _dry_run_service
    if _dry_run_service is None:
        db = DatabaseConnection()
        _dry_run_service = DryRunModeService(db.get_connection())
    return _dry_run_service


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


def load_pending_jobs_metrics() -> tuple[list[list[Any]], dict[str, Any]]:
    """
    Load pending jobs metrics from database.

    Returns:
        Tuple of (pending_jobs_data, error_summary_data)
    """
    try:
        service = get_pending_service()

        # Get pending jobs
        jobs = service.get_pending_jobs(limit=20)
        pending_jobs_data = [[job.get("job_id", "N/A"), job.get("job_title", "N/A"), job.get("company_name", "N/A"), job.get("platform", "N/A"), job.get("error_type", "unknown"), job.get("error_message", "No error info")] for job in jobs]

        # Get error summary
        summary = service.get_error_summary()
        error_summary_data = {"error_type": list(summary.keys()), "count": list(summary.values())}

        logger.debug(f"[gradio_app] Pending jobs loaded: {len(pending_jobs_data)} jobs")
        return (pending_jobs_data, error_summary_data)

    except Exception as e:
        logger.error(f"[gradio_app] Error loading pending jobs metrics: {e}")
        return ([], {"error_type": [], "count": []})


def handle_retry_job(job_id_input: str) -> str:
    """Handle retry job action."""
    try:
        if not job_id_input or job_id_input.strip() == "":
            return "❌ Please enter a Job ID"

        service = get_pending_service()
        result = service.retry_job(job_id_input.strip())

        if result["success"]:
            return f"✅ {result['message']}: {result['job_id']}"
        else:
            return f"❌ {result['message']}"
    except Exception as e:
        logger.error(f"[gradio_app] Error retrying job: {e}")
        return f"❌ Error: {e!s}"


def handle_skip_job(job_id_input: str, reason_input: str) -> str:
    """Handle skip job action."""
    try:
        if not job_id_input or job_id_input.strip() == "":
            return "❌ Please enter a Job ID"

        if not reason_input or reason_input.strip() == "":
            reason_input = "User skipped"

        service = get_pending_service()
        result = service.skip_job(job_id_input.strip(), reason_input.strip())

        if result["success"]:
            return f"✅ {result['message']}: {result['job_id']}"
        else:
            return f"❌ {result['message']}"
    except Exception as e:
        logger.error(f"[gradio_app] Error skipping job: {e}")
        return f"❌ Error: {e!s}"


def handle_manual_complete(job_id_input: str) -> str:
    """Handle manual complete action."""
    try:
        if not job_id_input or job_id_input.strip() == "":
            return "❌ Please enter a Job ID"

        service = get_pending_service()
        result = service.mark_manual_complete(job_id_input.strip())

        if result["success"]:
            return f"✅ {result['message']}: {result['job_id']}"
        else:
            return f"❌ {result['message']}"
    except Exception as e:
        logger.error(f"[gradio_app] Error marking job as complete: {e}")
        return f"❌ Error: {e!s}"


def create_pending_tab() -> gr.Blocks:
    """
    Create the pending jobs management tab.

    Returns:
        Gradio Blocks component
    """
    with gr.Column() as pending:
        gr.Markdown("# ⏸️ Pending Jobs")
        gr.Markdown("Manage jobs requiring manual intervention")

        pending_jobs_table = gr.Dataframe(value=[], headers=["Job ID", "Title", "Company", "Platform", "Error Type", "Error Message"], label="Pending Jobs (Last 20)")

        gr.Markdown("### Actions")
        gr.Markdown("Copy a Job ID from the table above to perform an action")

        with gr.Row():
            job_id_input = gr.Textbox(label="Job ID", placeholder="Enter job ID from table above")

        with gr.Row():
            retry_btn = gr.Button("🔄 Retry", variant="primary", scale=1)
            skip_btn = gr.Button("⏭️ Skip", variant="secondary", scale=1)
            complete_btn = gr.Button("✅ Manual Complete", scale=1)

        with gr.Row():
            skip_reason_input = gr.Textbox(label="Skip Reason (optional)", placeholder="e.g., Not interested")

        action_status = gr.Textbox(label="Action Status", value="", interactive=False)

        gr.Markdown("### Error Summary")
        error_summary_chart = gr.BarPlot(value={"error_type": [], "count": []}, x="error_type", y="count", title="Errors by Type", height=250)

        # Refresh button
        refresh_btn = gr.Button("🔄 Refresh Pending Jobs", variant="secondary")

        # Auto-refresh timer (every 30 seconds)
        timer = gr.Timer(30)

        # Wire up refresh logic
        refresh_outputs = [pending_jobs_table, error_summary_chart]

        refresh_btn.click(fn=load_pending_jobs_metrics, outputs=refresh_outputs)
        timer.tick(fn=load_pending_jobs_metrics, outputs=refresh_outputs)

        # Wire up action buttons
        retry_btn.click(fn=handle_retry_job, inputs=[job_id_input], outputs=[action_status])
        skip_btn.click(fn=handle_skip_job, inputs=[job_id_input, skip_reason_input], outputs=[action_status])
        complete_btn.click(fn=handle_manual_complete, inputs=[job_id_input], outputs=[action_status])

        # Load initial data
        pending.load(fn=load_pending_jobs_metrics, outputs=refresh_outputs)

    return pending


def load_approval_metrics() -> tuple[bool, int, float, int, list[list[Any]]]:
    """
    Load approval mode metrics and pending approvals.

    Returns:
        Tuple of (enabled, pending_count, avg_match_score, oldest_job_days, approvals_data)
    """
    try:
        service = get_approval_service()
        summary = service.get_approval_summary()
        approvals = service.get_pending_approvals()

        # Format pending approvals for dataframe
        approvals_data = [
            [
                approval.get("job_id", ""),
                approval.get("job_title", "N/A"),
                approval.get("company_name", "N/A"),
                approval.get("platform", "N/A"),
                f"{approval.get('match_score', 0.0):.2f}",
                approval.get("created_at").strftime("%Y-%m-%d %H:%M") if approval.get("created_at") else "N/A",
            ]
            for approval in approvals
        ]

        return (summary["approval_mode_enabled"], summary["pending_count"], summary["avg_match_score"], summary["oldest_job_days"], approvals_data)

    except Exception as e:
        logger.error(f"[gradio_app] Error loading approval metrics: {e}")
        return (False, 0, 0.0, 0, [])


def handle_toggle_approval_mode(enabled: bool) -> str:
    """Handle approval mode toggle action."""
    try:
        service = get_approval_service()
        success = service.set_approval_mode(enabled)

        if success:
            mode = "enabled" if enabled else "disabled"
            return f"✅ Approval mode {mode}"
        else:
            return "❌ Failed to update approval mode"

    except Exception as e:
        logger.error(f"[gradio_app] Error toggling approval mode: {e}")
        return f"❌ Error: {e!s}"


def handle_approve_job(job_id_input: str) -> str:
    """Handle approve job action."""
    try:
        if not job_id_input or job_id_input.strip() == "":
            return "❌ Please enter a Job ID"

        service = get_approval_service()
        result = service.approve_job(job_id_input.strip())

        if result["success"]:
            return f"✅ {result['message']}: {result['job_id']}"
        else:
            return f"❌ {result['message']}"

    except Exception as e:
        logger.error(f"[gradio_app] Error approving job: {e}")
        return f"❌ Error: {e!s}"


def handle_reject_job_approval(job_id_input: str, reason: str) -> str:
    """Handle reject job action."""
    try:
        if not job_id_input or job_id_input.strip() == "":
            return "❌ Please enter a Job ID"

        if not reason or reason.strip() == "":
            return "❌ Please enter a rejection reason"

        service = get_approval_service()
        result = service.reject_job(job_id_input.strip(), reason.strip())

        if result["success"]:
            return f"✅ {result['message']}: {result['job_id']}"
        else:
            return f"❌ {result['message']}"

    except Exception as e:
        logger.error(f"[gradio_app] Error rejecting job: {e}")
        return f"❌ Error: {e!s}"


def create_approval_tab() -> gr.Blocks:
    """
    Create the approval mode tab.

    Returns:
        Gradio Blocks component
    """
    with gr.Column() as approval:
        gr.Markdown("# ✅ Approval Mode")
        gr.Markdown("Review and approve applications before submission")

        # Approval mode toggle
        gr.Markdown("### Approval Mode Settings")
        with gr.Row():
            approval_toggle = gr.Checkbox(label="Require approval before sending applications", value=False, interactive=True)
            toggle_status = gr.Textbox(label="Status", value="", interactive=False, scale=2)

        # Summary metrics
        gr.Markdown("### Approval Summary")
        with gr.Row():
            pending_count_metric = gr.Number(label="Pending Approvals", value=0, interactive=False)
            avg_score_metric = gr.Number(label="Avg Match Score", value=0.0, interactive=False)
            oldest_days_metric = gr.Number(label="Oldest Job (Days)", value=0, interactive=False)

        # Pending approvals list
        gr.Markdown("### Pending Approvals")
        approvals_table = gr.Dataframe(value=[], headers=["Job ID", "Title", "Company", "Platform", "Match Score", "Created"], label="Jobs Awaiting Approval (Max 20)")

        # Action buttons
        gr.Markdown("### Actions")
        with gr.Row():
            job_id_input = gr.Textbox(label="Job ID", placeholder="Enter job ID...", scale=2)

        with gr.Row():
            approve_btn = gr.Button("✅ Approve", variant="primary")
            reject_btn = gr.Button("❌ Reject", variant="secondary")

        with gr.Row():
            rejection_reason = gr.Textbox(label="Rejection Reason", placeholder="Enter reason for rejection...", scale=2)

        action_status = gr.Textbox(label="Action Status", value="", interactive=False)

        # Refresh controls
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh", variant="secondary")

        # Auto-refresh timer (30 seconds)
        timer = gr.Timer(30)

        # Wire up toggle logic
        approval_toggle.change(fn=handle_toggle_approval_mode, inputs=[approval_toggle], outputs=[toggle_status])

        # Wire up refresh logic
        refresh_outputs = [approval_toggle, pending_count_metric, avg_score_metric, oldest_days_metric, approvals_table]

        refresh_btn.click(fn=load_approval_metrics, outputs=refresh_outputs)
        timer.tick(fn=load_approval_metrics, outputs=refresh_outputs)

        # Wire up action buttons
        approve_btn.click(fn=handle_approve_job, inputs=[job_id_input], outputs=[action_status])
        reject_btn.click(fn=handle_reject_job_approval, inputs=[job_id_input, rejection_reason], outputs=[action_status])

        # Load initial data
        approval.load(fn=load_approval_metrics, outputs=refresh_outputs)

    return approval


def load_dry_run_metrics() -> tuple[bool, int, float, int, list[list[Any]]]:
    """
    Load dry-run mode metrics and dry-run results.

    Returns:
        Tuple of (enabled, dry_run_count, avg_match_score, newest_job_hours, results_data)
    """
    try:
        service = get_dry_run_service()
        analytics = service.get_dry_run_analytics()
        results = service.get_dry_run_results()

        # Format dry-run results for dataframe
        results_data = [
            [
                result.get("job_id", ""),
                result.get("job_title", "N/A"),
                result.get("company_name", "N/A"),
                result.get("platform", "N/A"),
                f"{result.get('match_score', 0.0):.2f}",
                result.get("created_at").strftime("%Y-%m-%d %H:%M") if result.get("created_at") else "N/A",
            ]
            for result in results
        ]

        return (analytics["dry_run_mode_enabled"], analytics["dry_run_count"], analytics["avg_match_score"], analytics["newest_job_hours"], results_data)

    except Exception as e:
        logger.error(f"[gradio_app] Error loading dry-run metrics: {e}")
        return (False, 0, 0.0, 0, [])


def handle_toggle_dry_run_mode(enabled: bool) -> str:
    """Handle dry-run mode toggle action."""
    try:
        service = get_dry_run_service()
        success = service.set_dry_run_mode(enabled)

        if success:
            mode = "enabled" if enabled else "disabled"
            return f"✅ Dry-run mode {mode}"
        else:
            return "❌ Failed to update dry-run mode"

    except Exception as e:
        logger.error(f"[gradio_app] Error toggling dry-run mode: {e}")
        return f"❌ Error: {e!s}"


def handle_send_now(job_id_input: str) -> str:
    """Handle send now action."""
    try:
        if not job_id_input or job_id_input.strip() == "":
            return "❌ Please enter a Job ID"

        service = get_dry_run_service()
        result = service.send_now(job_id_input.strip())

        if result["success"]:
            return f"✅ {result['message']}: {result['job_id']}"
        else:
            return f"❌ {result['message']}"

    except Exception as e:
        logger.error(f"[gradio_app] Error sending job: {e}")
        return f"❌ Error: {e!s}"


def create_dry_run_tab() -> gr.Blocks:
    """
    Create the dry-run mode tab.

    Returns:
        Gradio Blocks component
    """
    with gr.Column() as dry_run:
        gr.Markdown("# 🧪 Dry-Run Mode")
        gr.Markdown("Test the system without sending real applications")

        # Dry-run mode toggle
        gr.Markdown("### Dry-Run Mode Settings")
        with gr.Row():
            dry_run_toggle = gr.Checkbox(label="Dry-run mode (generate but don't send)", value=False, interactive=True)
            toggle_status = gr.Textbox(label="Status", value="", interactive=False, scale=2)

        # Analytics metrics
        gr.Markdown("### Dry-Run Analytics")
        with gr.Row():
            dry_run_count_metric = gr.Number(label="Dry-Run Jobs", value=0, interactive=False)
            avg_score_metric = gr.Number(label="Avg Match Score", value=0.0, interactive=False)
            newest_hours_metric = gr.Number(label="Newest Job (Hours Ago)", value=0, interactive=False)

        # Dry-run results list
        gr.Markdown("### Dry-Run Results")
        results_table = gr.Dataframe(value=[], headers=["Job ID", "Title", "Company", "Platform", "Match Score", "Created"], label="Dry-Run Jobs (Max 20)")

        # Action button
        gr.Markdown("### Actions")
        with gr.Row():
            job_id_input = gr.Textbox(label="Job ID", placeholder="Enter job ID to send...", scale=2)

        with gr.Row():
            send_now_btn = gr.Button("📤 Send Now", variant="primary")

        action_status = gr.Textbox(label="Action Status", value="", interactive=False)

        # Refresh controls
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh", variant="secondary")

        # Auto-refresh timer (30 seconds)
        timer = gr.Timer(30)

        # Wire up toggle logic
        dry_run_toggle.change(fn=handle_toggle_dry_run_mode, inputs=[dry_run_toggle], outputs=[toggle_status])

        # Wire up refresh logic
        refresh_outputs = [dry_run_toggle, dry_run_count_metric, avg_score_metric, newest_hours_metric, results_table]

        refresh_btn.click(fn=load_dry_run_metrics, outputs=refresh_outputs)
        timer.tick(fn=load_dry_run_metrics, outputs=refresh_outputs)

        # Wire up action button
        send_now_btn.click(fn=handle_send_now, inputs=[job_id_input], outputs=[action_status])

        # Load initial data
        dry_run.load(fn=load_dry_run_metrics, outputs=refresh_outputs)

    return dry_run


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

            with gr.Tab("Approval Mode"):
                create_approval_tab()

            with gr.Tab("Dry-Run Mode"):
                create_dry_run_tab()

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
