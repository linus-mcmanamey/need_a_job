#!/bin/bash
# Health check script for Docker containers
# Checks if the application is running and responding

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
TIMEOUT="${TIMEOUT:-5}"

# Function to check API health
check_api_health() {
    local url="$API_URL$HEALTH_ENDPOINT"

    if command -v curl &> /dev/null; then
        response=$(curl -sf --max-time "$TIMEOUT" "$url" 2>&1)
        exit_code=$?
    elif command -v wget &> /dev/null; then
        response=$(wget -qO- --timeout="$TIMEOUT" "$url" 2>&1)
        exit_code=$?
    else
        echo -e "${RED}ERROR: Neither curl nor wget is available${NC}"
        exit 1
    fi

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ API is healthy${NC}"
        echo "Response: $response"
        return 0
    else
        echo -e "${RED}✗ API health check failed${NC}"
        echo "Error: $response"
        return 1
    fi
}

# Function to check Redis connectivity
check_redis() {
    local redis_host="${REDIS_HOST:-localhost}"
    local redis_port="${REDIS_PORT:-6379}"

    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$redis_host" -p "$redis_port" ping > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Redis is reachable${NC}"
            return 0
        else
            echo -e "${RED}✗ Redis is not reachable${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ redis-cli not available, skipping Redis check${NC}"
        return 0
    fi
}

# Function to check DuckDB file
check_database() {
    local db_path="${DUCKDB_PATH:-/app/data/job_applications.duckdb}"

    if [ -f "$db_path" ]; then
        echo -e "${GREEN}✓ Database file exists${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ Database file not found (will be created on first use)${NC}"
        return 0
    fi
}

# Main health check routine
main() {
    echo "=== Job Application Automation System Health Check ==="
    echo "Timestamp: $(date)"
    echo ""

    local exit_code=0

    # Check API health (required)
    if ! check_api_health; then
        exit_code=1
    fi
    echo ""

    # Check Redis (optional for API, required for workers)
    if ! check_redis; then
        if [ "$CHECK_REDIS" = "required" ]; then
            exit_code=1
        fi
    fi
    echo ""

    # Check database (informational)
    check_database
    echo ""

    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}=== All health checks passed ===${NC}"
    else
        echo -e "${RED}=== Some health checks failed ===${NC}"
    fi

    exit $exit_code
}

# Run main function
main "$@"
