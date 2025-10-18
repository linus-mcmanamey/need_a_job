#!/bin/bash
# Start LinkedIn MCP Server with cookie from .env file

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load environment variables from .env file
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | xargs)
else
    echo "Error: .env file not found at $SCRIPT_DIR/.env"
    exit 1
fi

# Check if LINKEDIN_COOKIE is set
if [ -z "$LINKEDIN_COOKIE" ]; then
    echo "Error: LINKEDIN_COOKIE not found in .env file"
    exit 1
fi

# Start the MCP server
cd "$SCRIPT_DIR/linkedin-mcp-server"

echo "Starting LinkedIn MCP Server..."
echo "Cookie loaded from .env file"
echo "Server will be available at: http://0.0.0.0:8080/mcp"

.venv/bin/python -m linkedin_mcp_server \
  --transport streamable-http \
  --host 0.0.0.0 \
  --port 8080 \
  --path /mcp \
  --cookie "$LINKEDIN_COOKIE" \
  --log-level INFO
