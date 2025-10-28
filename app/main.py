"""
FastAPI application entry point for the Job Application Automation System.

This module sets up the FastAPI application with all routes, middleware,
and configuration needed for the REST API.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger


# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logger.add(
    "logs/app.log",
    rotation="1 day",
    retention="30 days",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
    level=log_level,
)


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

# Configure CORS middleware for Gradio integration
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:7860,http://localhost:8000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    except Exception as e:
        logger.error(f"Health check - database error: {e}")
        db_status = "error"

    health_data = {
        "status": "healthy",
        "service": "job-automation-api",
        "version": "1.0.0-mvp",
        "environment": os.getenv("APP_ENV", "development"),
        "database": {"status": db_status},
    }

    logger.debug(f"Health check: {health_data}")
    return JSONResponse(content=health_data, status_code=200)


@app.get("/", tags=["System"])
async def root() -> dict:
    """
    Root endpoint.

    Returns:
        Welcome message and links
    """
    return {
        "message": "Job Application Automation System API",
        "version": "1.0.0-mvp",
        "docs": "/api/docs",
        "health": "/health",
        "config": "/api/config",
        "gradio_ui": "http://localhost:7860",
    }


@app.get("/api/config", tags=["Configuration"])
async def get_configuration() -> dict:
    """
    Get current configuration (sanitized).

    Returns:
        Sanitized configuration data
    """
    from app.config import get_config

    config = get_config()

    return {
        "search": {
            "job_type": config.search.get("job_type"),
            "duration": config.search.get("duration"),
        },
        "agents": list(config.agents.keys()),
        "platforms": list(config.platforms.keys()),
    }


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

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level.lower(),
    )


if __name__ == "__main__":
    start()
