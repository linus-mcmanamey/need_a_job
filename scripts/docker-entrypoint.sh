#!/bin/bash
# Docker entrypoint script for Job Application Automation System
# Handles initialization and graceful startup

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to wait for Redis
wait_for_redis() {
    local redis_host="${REDIS_HOST:-redis}"
    local redis_port="${REDIS_PORT:-6379}"
    local max_attempts=30
    local attempt=0

    log_info "Waiting for Redis at ${redis_host}:${redis_port}..."

    while [ $attempt -lt $max_attempts ]; do
        if redis-cli -h "$redis_host" -p "$redis_port" ping > /dev/null 2>&1; then
            log_success "Redis is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        log_info "Redis not ready yet (attempt $attempt/$max_attempts)..."
        sleep 2
    done

    log_error "Redis failed to become ready after $max_attempts attempts"
    return 1
}

# Function to initialize database
init_database() {
    local db_path="${DUCKDB_PATH:-/app/data/job_applications.duckdb}"
    local schema_file="/app/app/database/schema.sql"

    log_info "Checking database at $db_path..."

    # Create data directory if it doesn't exist
    mkdir -p "$(dirname "$db_path")"

    # Check if database exists and has tables
    if [ -f "$db_path" ]; then
        log_info "Database file exists"
        # Could add table existence check here
    else
        log_warning "Database file not found, will be created on first use"
        # If schema file exists, we could initialize it here
        if [ -f "$schema_file" ]; then
            log_info "Initializing database schema..."
            # Add initialization logic here if needed
        fi
    fi
}

# Function to create required directories
create_directories() {
    log_info "Creating required directories..."

    local dirs=(
        "/app/data"
        "/app/logs"
        "/app/export_cv_cover_letter"
        "/app/second_folder"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done

    log_success "Directory structure ready"
}

# Function to check environment variables
check_env_vars() {
    log_info "Checking required environment variables..."

    local required_vars=(
        "ANTHROPIC_API_KEY"
        "REDIS_URL"
    )

    local missing_vars=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        log_warning "Missing environment variables: ${missing_vars[*]}"
        log_warning "Some features may not work correctly"
    else
        log_success "All required environment variables are set"
    fi
}

# Function to display startup banner
show_banner() {
    cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     Job Application Automation System - Phase 1             ║
║     FastAPI + Redis + RQ + DuckDB + Gradio                  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
}

# Main entrypoint function
main() {
    show_banner
    echo ""

    log_info "Starting initialization..."
    log_info "Environment: ${APP_ENV:-development}"
    log_info "Log level: ${LOG_LEVEL:-INFO}"
    echo ""

    # Check environment variables
    check_env_vars
    echo ""

    # Create directories
    create_directories
    echo ""

    # Initialize database
    init_database
    echo ""

    # Wait for Redis (if not running in standalone mode)
    if [ "${SKIP_REDIS_CHECK}" != "true" ]; then
        wait_for_redis || {
            log_error "Failed to connect to Redis"
            exit 1
        }
        echo ""
    fi

    log_success "Initialization complete"
    echo ""

    # Execute the main command
    log_info "Starting application: $*"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    exec "$@"
}

# Run main function with all arguments
main "$@"
