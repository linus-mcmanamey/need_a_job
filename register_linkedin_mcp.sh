#!/bin/bash
# Register LinkedIn MCP Server with Claude Code

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Load the LinkedIn cookie from .env
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
else
    echo "Error: .env file not found at $PROJECT_DIR/.env"
    exit 1
fi

if [ -z "$LINKEDIN_COOKIE" ]; then
    echo "Error: LINKEDIN_COOKIE not found in .env file"
    exit 1
fi

echo "=========================================="
echo "Registering LinkedIn MCP Server with Claude Code"
echo "=========================================="
echo ""

# Method 1: Using stdio transport (recommended)
echo "Attempting to add LinkedIn MCP server..."
echo ""

# Use claude mcp add command with the cookie from environment
LINKEDIN_COOKIE="$LINKEDIN_COOKIE" claude mcp add linkedin \
    -e LINKEDIN_COOKIE="$LINKEDIN_COOKIE" \
    -- "$PROJECT_DIR/linkedin-mcp-server/.venv/bin/python" \
    -m linkedin_mcp_server \
    --cookie "\$LINKEDIN_COOKIE"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ LinkedIn MCP Server registered successfully!"
    echo ""
    echo "You can now use LinkedIn tools in Claude Code:"
    echo "  - Get job recommendations"
    echo "  - Research LinkedIn profiles"
    echo "  - Analyze companies"
    echo "  - Search for jobs"
    echo ""
    echo "Try asking Claude:"
    echo "  'What are my recommended jobs on LinkedIn?'"
    echo ""
else
    echo ""
    echo "❌ Failed to register LinkedIn MCP server"
    echo ""
    echo "Manual registration:"
    echo "Run this command:"
    echo ""
    echo "claude mcp add linkedin -e LINKEDIN_COOKIE=\"$LINKEDIN_COOKIE\" -- $PROJECT_DIR/linkedin-mcp-server/.venv/bin/python -m linkedin_mcp_server --cookie \"\\\$LINKEDIN_COOKIE\""
    echo ""
fi

echo "=========================================="
