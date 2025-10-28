# Multi-stage Dockerfile for Job Application Automation System
# Base image: Python 3.11-slim for production-ready deployment
# Supports both API and worker modes

# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential build tools
    build-essential \
    curl \
    wget \
    git \
    # For document processing (python-docx)
    libxml2 \
    libxslt1.1 \
    # For networking and SSL
    ca-certificates \
    openssl \
    # For potential browser automation (V2)
    # chromium chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Set working directory
WORKDIR /app

# Stage 2: Poetry dependencies installation
FROM base as builder

# Install Poetry for dependency management
ENV POETRY_VERSION=1.7.0 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies (without dev dependencies for production)
RUN --mount=type=cache,target=$POETRY_CACHE_DIR \
    poetry install --no-root --only main && \
    rm -rf $POETRY_CACHE_DIR

# Stage 3: Application runtime (FastAPI + Gradio)
FROM base as app

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser ./app /app/app
COPY --chown=appuser:appuser ./config /app/config
COPY --chown=appuser:appuser ./.mcp.json /app/.mcp.json

# Create necessary directories with correct permissions
RUN mkdir -p /app/data /app/logs /app/current_cv_coverletter /app/export_cv_cover_letter /app/second_folder && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run FastAPI with uvicorn (Gradio UI embedded in FastAPI app)
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# Stage 4: RQ Worker runtime
FROM base as worker

# Copy installed dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=appuser:appuser ./app /app/app
COPY --chown=appuser:appuser ./config /app/config
COPY --chown=appuser:appuser ./.mcp.json /app/.mcp.json

# Create necessary directories with correct permissions
RUN mkdir -p /app/data /app/logs /app/current_cv_coverletter /app/export_cv_cover_letter /app/second_folder && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Run RQ worker
# Worker processes discovery_queue, pipeline_queue, and submission_queue
CMD ["rq", "worker", "--url", "redis://redis:6379", "discovery_queue", "pipeline_queue", "submission_queue"]

# Stage 5: Development image (with dev dependencies and hot reload)
FROM base as development

# Install Poetry
ENV POETRY_VERSION=1.7.0 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /opt/poetry/bin/poetry /usr/local/bin/poetry

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install all dependencies (including dev)
RUN poetry install --no-root

# Copy application code
COPY --chown=appuser:appuser . /app

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/current_cv_coverletter /app/export_cv_cover_letter /app/second_folder && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 8000 7860

# Run with hot reload for development
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
