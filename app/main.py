"""
FastAPI application entry point for the Job Application Automation System.

This module sets up the FastAPI application with all routes, middleware,
and configuration needed for the REST API.
"""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
app_env = os.getenv("APP_ENV", "development")

# Only log to file in non-test environments to avoid permission issues in CI/CD
if app_env != "test":
    try:
        logger.add("logs/app.log", rotation="1 day", retention="30 days", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}", level=log_level)
    except PermissionError:
        # If we can't write to logs directory, just log to stderr
        logger.warning("Cannot write to logs/app.log, logging to stderr only")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for application startup and shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    # Startup
    logger.info("Starting Job Application Automation System API")
    logger.info(f"Environment: {os.getenv('APP_ENV', 'development')}")
    logger.info(f"Log level: {log_level}")

    # Initialize database connection
    try:
        from app.repositories.database import initialize_database

        initialize_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")

    yield

    # Shutdown
    logger.info("Shutting down Job Application Automation System API")


# Create FastAPI application
app = FastAPI(
    title="Job Application Automation System",
    description="Automated job search and application system for Data Engineering roles",
    version="1.0.0-mvp",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Configure CORS middleware for Vue 3 frontend integration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174,http://localhost:8000")
app.add_middleware(CORSMiddleware, allow_origins=allowed_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/health", tags=["System"])
async def health_check() -> JSONResponse:
    """
    Health check endpoint.

    Returns:
        JSON response with health status
    """
    from app.repositories.database import get_database_info

    try:
        db_info = get_database_info()
        db_status = "connected" if db_info["exists"] else "not_initialized"
        table_count = db_info.get("table_count", 0)
    except Exception as e:
        logger.error(f"Health check - database error: {e}")
        db_status = "error"
        table_count = 0

    health_data = {"status": "healthy", "service": "job-automation-api", "version": "1.0.0-mvp", "environment": os.getenv("APP_ENV", "development"), "database": {"status": db_status, "tables": table_count}}

    logger.debug(f"Health check: {health_data}")
    return JSONResponse(content=health_data, status_code=200)


@app.get("/", tags=["System"])
async def root() -> dict:
    """
    Root endpoint.

    Returns:
        Welcome message and links
    """
    return {"message": "Job Application Automation System API", "version": "1.0.0-mvp", "docs": "/api/docs", "health": "/health", "config": "/api/config", "frontend_ui": "http://localhost:5173"}


@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for real-time status updates.

    Clients can connect to this endpoint to receive real-time updates about
    job status changes, pipeline metrics, and other system events.

    Args:
        websocket: The WebSocket connection
    """
    from app.ui.websocket import manager

    await manager.connect(websocket)
    try:
        while True:
            # Wait for messages from client (if any)
            # In this implementation, we primarily use server-to-client broadcasting
            data = await websocket.receive_text()
            logger.debug(f"Received WebSocket message: {data}")
            # Echo or handle client messages if needed
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")


@app.get("/api/config", tags=["Configuration"])
async def get_configuration() -> dict:
    """
    Get current configuration (sanitized).

    Returns:
        Sanitized configuration data
    """
    from app.config import get_config
    from app.repositories.database import get_database_info

    config = get_config()

    return {"search": {"job_type": config.search.get("job_type"), "duration": config.search.get("duration")}, "agents": list(config.agents.keys()), "platforms": list(config.platforms.keys()), "database": get_database_info()}


@app.get("/api/config/search", tags=["Configuration"])
async def get_search_configuration() -> dict:
    """
    Get full search configuration.

    Returns:
        Complete search configuration from search.yaml
    """
    from app.config import get_config

    config = get_config()
    logger.debug("Returning search configuration")

    return config.search


@app.put("/api/config/search", tags=["Configuration"])
async def update_search_configuration(config_data: dict) -> dict:
    """
    Update search configuration.

    Args:
        config_data: Updated search configuration data

    Returns:
        Success message and updated configuration
    """
    from fastapi import HTTPException

    from app.config import get_config

    try:
        config = get_config()

        # Validate that required fields exist
        required_fields = ["job_type", "duration", "locations", "keywords", "technologies", "salary_expectations"]
        for field in required_fields:
            if field not in config_data:
                raise ValueError(f"Missing required field: {field}")

        # Save the configuration
        config.save_yaml("search.yaml", config_data)

        logger.info("Search configuration updated successfully")
        return {"success": True, "message": "Configuration updated successfully", "config": config.search}

    except ValueError as e:
        logger.error(f"Validation error updating search config: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        logger.error(f"Permission error updating search config: {e}")
        raise HTTPException(status_code=500, detail="Unable to save configuration file. Check file permissions.")
    except Exception as e:
        logger.error(f"Error updating search configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update configuration: {str(e)}")


@app.get("/api/jobs", tags=["Jobs"])
async def list_jobs(platform: str | None = None, limit: int = 20, offset: int = 0) -> dict:
    """
    List jobs with optional filtering.

    Args:
        platform: Filter by platform source (linkedin, seek, indeed)
        limit: Maximum number of jobs to return (default: 20, max: 100)
        offset: Number of jobs to skip for pagination

    Returns:
        List of jobs with pagination info
    """
    from app.repositories.jobs_repository import JobsRepository

    # Validate limit
    limit = min(limit, 100)

    filters = {}
    if platform:
        filters["platform_source"] = platform

    repo = JobsRepository()
    jobs = repo.list_jobs(filters=filters, limit=limit, offset=offset)
    total = repo.count_jobs(filters=filters)

    return {"jobs": [job.to_dict() for job in jobs], "pagination": {"limit": limit, "offset": offset, "total": total, "has_more": (offset + len(jobs)) < total}}


@app.get("/api/jobs/{job_id}", tags=["Jobs"])
async def get_job(job_id: str) -> dict:
    """
    Get a specific job by ID.

    Args:
        job_id: The job ID to retrieve

    Returns:
        Job details
    """
    from fastapi import HTTPException

    from app.repositories.jobs_repository import JobsRepository

    repo = JobsRepository()
    job = repo.get_job_by_id(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job.to_dict()


@app.get("/api/applications", tags=["Applications"])
async def list_applications(status: str | None = None, limit: int = 20, offset: int = 0) -> dict:
    """
    List applications with optional filtering.

    Args:
        status: Filter by application status
        limit: Maximum number of applications to return (default: 20, max: 100)
        offset: Number of applications to skip for pagination

    Returns:
        List of applications with pagination info
    """
    from app.repositories.application_repository import ApplicationRepository

    # Validate limit
    limit = min(limit, 100)

    filters = {}
    if status:
        filters["status"] = status

    repo = ApplicationRepository()
    applications = repo.list_applications(filters=filters, limit=limit, offset=offset)
    total = repo.count_applications(filters=filters)

    return {"applications": [app.to_dict() for app in applications], "pagination": {"limit": limit, "offset": offset, "total": total, "has_more": (offset + len(applications)) < total}}


@app.get("/api/applications/{application_id}", tags=["Applications"])
async def get_application(application_id: str) -> dict:
    """
    Get a specific application by ID.

    Args:
        application_id: The application ID to retrieve

    Returns:
        Application details
    """
    from fastapi import HTTPException

    from app.repositories.application_repository import ApplicationRepository

    repo = ApplicationRepository()
    application = repo.get_application_by_id(application_id)

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    return application.to_dict()


@app.post("/api/jobs/{job_id}/retry", tags=["Jobs"])
async def retry_job(job_id: str) -> dict:
    """
    Retry a failed or pending job.

    Args:
        job_id: The job ID to retry

    Returns:
        Result of retry operation
    """
    from fastapi import HTTPException

    from app.models.api_requests import RetryJobRequest
    from app.repositories.database import get_db_connection
    from app.services.pending_jobs import PendingJobsService
    from app.ui.websocket import manager

    # Validate input
    try:
        request = RetryJobRequest(job_id=job_id)
        validated_job_id = request.job_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid job_id: {str(e)}")

    try:
        db = get_db_connection()
        service = PendingJobsService(db)
        result = service.retry_job(validated_job_id)

        # Broadcast WebSocket update
        await manager.broadcast({"type": "job_retry", "job_id": validated_job_id, "status": result.get("status")})

        logger.info(f"Job {validated_job_id} retry requested")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrying job {validated_job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/pipeline", tags=["Pipeline"])
async def get_pipeline_status() -> dict:
    """
    Get current pipeline status and metrics.

    Returns:
        Pipeline metrics including active jobs, stage counts, and bottlenecks
    """
    from app.repositories.database import get_db_connection
    from app.services.pipeline_metrics import PipelineMetricsService

    try:
        db = get_db_connection()
        service = PipelineMetricsService(db)

        active_jobs = service.get_active_jobs_in_pipeline()
        stage_counts = service.get_pipeline_stage_counts()

        return {"active_jobs": active_jobs, "stage_counts": stage_counts, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        return {"active_jobs": [], "stage_counts": {}, "error": str(e)}


@app.get("/api/pending", tags=["Pending"])
async def list_pending_jobs(limit: int = 20) -> dict:
    """
    List jobs requiring manual intervention.

    Args:
        limit: Maximum number of jobs to return

    Returns:
        List of pending jobs with error details
    """
    from app.repositories.database import get_db_connection
    from app.services.pending_jobs import PendingJobsService

    try:
        db = get_db_connection()
        service = PendingJobsService(db)

        jobs = service.get_pending_jobs(limit=limit)
        return {"pending_jobs": jobs, "count": len(jobs)}
    except Exception as e:
        logger.error(f"Error listing pending jobs: {e}")
        return {"pending_jobs": [], "count": 0, "error": str(e)}


@app.post("/api/pending/{job_id}/approve", tags=["Pending"])
async def approve_pending_job(job_id: str) -> dict:
    """
    Approve a pending job for submission.

    Args:
        job_id: The job ID to approve

    Returns:
        Result of approve operation
    """
    from fastapi import HTTPException

    from app.models.api_requests import ApproveJobRequest
    from app.repositories.database import get_db_connection
    from app.services.approval_mode import ApprovalModeService
    from app.ui.websocket import manager

    # Validate input
    try:
        request = ApproveJobRequest(job_id=job_id)
        validated_job_id = request.job_id
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid job_id: {str(e)}")

    try:
        db = get_db_connection()
        service = ApprovalModeService(db)
        result = service.approve_job(validated_job_id)

        # Broadcast WebSocket update
        await manager.broadcast({"type": "job_update", "job_id": validated_job_id, "status": "approved", "action": "approve"})

        logger.info(f"Job {validated_job_id} approved")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving job {validated_job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/pending/{job_id}/reject", tags=["Pending"])
async def reject_pending_job(job_id: str, reason: str = "User rejected") -> dict:
    """
    Reject a pending job.

    Args:
        job_id: The job ID to reject
        reason: Optional reason for rejection

    Returns:
        Result of reject operation
    """
    from fastapi import HTTPException

    from app.models.api_requests import RejectJobRequest
    from app.repositories.database import get_db_connection
    from app.services.approval_mode import ApprovalModeService
    from app.ui.websocket import manager

    # Validate input
    try:
        request = RejectJobRequest(job_id=job_id, reason=reason)
        validated_job_id = request.job_id
        validated_reason = request.reason
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(e)}")

    try:
        db = get_db_connection()
        service = ApprovalModeService(db)
        result = service.reject_job(validated_job_id, validated_reason)

        # Broadcast WebSocket update
        await manager.broadcast({"type": "job_update", "job_id": validated_job_id, "status": "rejected", "action": "reject"})

        logger.info(f"Job {validated_job_id} rejected: {validated_reason}")
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting job {validated_job_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/api/discover", tags=["Jobs"])
async def discover_jobs() -> dict:
    """
    Trigger job discovery from configured job boards.

    Runs pollers for SEEK and Indeed based on search configuration.

    Returns:
        Discovery results with metrics from each poller
    """
    from fastapi import HTTPException

    from app.config import get_config
    from app.pollers.indeed_poller import IndeedPoller
    from app.pollers.seek_poller import SEEKPoller
    from app.repositories.application_repository import ApplicationRepository
    from app.repositories.jobs_repository import JobsRepository
    from app.ui.websocket import manager

    try:
        logger.info("Job discovery triggered via API")

        # Get configuration
        config = get_config()
        search_config = config.search

        # Initialize repositories
        jobs_repo = JobsRepository()
        app_repo = ApplicationRepository()

        results = {"status": "completed", "timestamp": datetime.now().isoformat(), "pollers": {}}

        # Run SEEK poller if enabled
        if search_config.get("seek", {}).get("enabled", False):
            try:
                logger.info("Starting SEEK poller...")
                seek_poller = SEEKPoller(config={"search": search_config, "seek": config.platforms.get("seek", {})}, jobs_repository=jobs_repo, application_repository=app_repo)
                seek_metrics = seek_poller.run_once()
                results["pollers"]["seek"] = seek_metrics
                logger.info(f"SEEK polling complete: {seek_metrics}")
            except Exception as e:
                logger.error(f"SEEK poller error: {e}")
                results["pollers"]["seek"] = {"error": str(e)}

        # Run Indeed poller if enabled
        if search_config.get("indeed", {}).get("enabled", False):
            try:
                logger.info("Starting Indeed poller...")
                indeed_poller = IndeedPoller(config={"search": search_config, "indeed": config.platforms.get("indeed", {})}, jobs_repository=jobs_repo, application_repository=app_repo)
                indeed_metrics = indeed_poller.run_once()
                results["pollers"]["indeed"] = indeed_metrics
                logger.info(f"Indeed polling complete: {indeed_metrics}")
            except Exception as e:
                logger.error(f"Indeed poller error: {e}")
                results["pollers"]["indeed"] = {"error": str(e)}

        # Broadcast WebSocket update
        await manager.broadcast({"type": "job_discovery_complete", "results": results})

        logger.info("Job discovery completed successfully")
        return results

    except Exception as e:
        logger.error(f"Error during job discovery: {e}")
        raise HTTPException(status_code=500, detail=f"Job discovery failed: {str(e)}")


@app.get("/api/history", tags=["Applications"])
async def get_application_history(
    platform: list[str] | None = Query(None),
    date_from: str | None = None,
    date_to: str | None = None,
    min_score: int | None = None,
    max_score: int | None = None,
    status: list[str] | None = Query(None),
    page: int = 1,
    page_size: int = 25,
    sort_by: str = "applied_date",
    sort_order: str = "desc",
) -> dict:
    """
    Get application history with filtering, sorting, and pagination.

    This endpoint returns a paginated list of completed applications with
    associated job details. Supports filtering by platform, date range,
    match score, and status. Results can be sorted by various columns.

    Args:
        platform: Filter by platforms (can be multiple, e.g., ?platform=linkedin&platform=seek)
        date_from: Start date (ISO format: YYYY-MM-DD)
        date_to: End date (ISO format: YYYY-MM-DD)
        min_score: Minimum match score (0-100)
        max_score: Maximum match score (0-100)
        status: Filter by status (can be multiple)
        page: Page number (starts at 1)
        page_size: Items per page (max 100)
        sort_by: Column to sort by (title, company, platform, applied_date, match_score, status)
        sort_order: Sort order (asc or desc)

    Returns:
        Paginated application history with job details
    """
    from fastapi import HTTPException
    from app.repositories.application_repository import ApplicationRepository

    try:
        # Validate parameters using Pydantic model
        from app.models.api_requests import HistoryFilterParams

        # FastAPI will automatically validate query params, but we instantiate
        # the model for additional validation
        params = HistoryFilterParams(platform=platform, date_from=date_from, date_to=date_to, min_score=min_score, max_score=max_score, status=status, page=page, page_size=page_size, sort_by=sort_by, sort_order=sort_order)

        # Get application history from repository
        repo = ApplicationRepository()
        applications, total = repo.get_application_history(
            platforms=params.platform,
            date_from=params.date_from,
            date_to=params.date_to,
            min_score=params.min_score,
            max_score=params.max_score,
            statuses=params.status,
            sort_by=params.sort_by,
            sort_order=params.sort_order,
            page=params.page,
            page_size=params.page_size,
        )

        logger.debug(f"Retrieved {len(applications)} applications (total: {total})")

        return {"applications": applications, "total": total, "page": params.page, "page_size": params.page_size}

    except ValueError as e:
        logger.error(f"Validation error in history endpoint: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving application history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Future API endpoints will be added here as routers
# from app.api.routes import jobs, pipeline, pending, approval, metrics
# app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
# app.include_router(pipeline.router, prefix="/api/pipeline", tags=["Pipeline"])
# app.include_router(pending.router, prefix="/api/pending", tags=["Pending"])
# app.include_router(approval.router, prefix="/api/approval", tags=["Approval"])
# app.include_router(metrics.router, prefix="/api/metrics", tags=["Metrics"])


def start() -> None:
    """
    Start the FastAPI application using uvicorn.

    This function is called when running the app with: poetry run start-api
    """
    import uvicorn

    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("APP_ENV", "development") == "development"

    logger.info(f"Starting FastAPI server on {host}:{port}")

    uvicorn.run("app.main:app", host=host, port=port, reload=reload, log_level=log_level.lower())


if __name__ == "__main__":
    start()
