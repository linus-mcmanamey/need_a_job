#!/bin/bash
# Wrapper script to run LinkedIn MCP Server with environment from .env

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env file
if [ -f "$SCRIPT_DIR/.env" ]; then
    source "$SCRIPT_DIR/.env"
fi

# Run the MCP server with the cookie
exec "$SCRIPT_DIR/linkedin-mcp-server/.venv/bin/python" -m linkedin_mcp_server --cookie "$LINKEDIN_COOKIE"
