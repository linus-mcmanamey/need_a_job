#!/bin/bash
# Helper script to add LinkedIn MCP server to Claude Code

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
echo "LinkedIn MCP Server Configuration"
echo "=========================================="
echo ""
echo "Add this configuration to your Claude Code MCP settings:"
echo ""
echo "Method 1: Using stdio (recommended for Claude Desktop)"
echo ""
cat << EOF
{
  "mcpServers": {
    "linkedin": {
      "command": "bash",
      "args": [
        "-c",
        "export LINKEDIN_COOKIE='$LINKEDIN_COOKIE' && $PROJECT_DIR/linkedin-mcp-server/.venv/bin/python -m linkedin_mcp_server --cookie \"\$LINKEDIN_COOKIE\""
      ]
    }
  }
}
EOF

echo ""
echo ""
echo "Method 2: Using environment variable (cleaner)"
echo ""
cat << EOF
{
  "mcpServers": {
    "linkedin": {
      "command": "$PROJECT_DIR/linkedin-mcp-server/.venv/bin/python",
      "args": [
        "-m",
        "linkedin_mcp_server",
        "--cookie",
        "$LINKEDIN_COOKIE"
      ]
    }
  }
}
EOF

echo ""
echo ""
echo "Method 3: Connect to running HTTP server"
echo "First start the server with: $PROJECT_DIR/start_linkedin_mcp.sh"
echo "Then use this configuration:"
echo ""
cat << EOF
{
  "mcpServers": {
    "linkedin": {
      "url": "http://localhost:8080/mcp",
      "transport": "streamable-http"
    }
  }
}
EOF

echo ""
echo "=========================================="
echo "To add to Claude Code:"
echo "1. Copy one of the configurations above"
echo "2. Open Claude Code settings"
echo "3. Find the MCP Servers section"
echo "4. Paste the configuration"
echo "5. Restart Claude Code"
echo "=========================================="
