#!/bin/bash
# Check LinkedIn MCP Server status

echo "=========================================="
echo "LinkedIn MCP Server Status"
echo "=========================================="
echo ""

# Check if server process is running
if pgrep -f "linkedin_mcp_server" > /dev/null; then
    echo "✅ Server Process: RUNNING"
    echo "   PID(s): $(pgrep -f linkedin_mcp_server | tr '\n' ' ')"
else
    echo "❌ Server Process: NOT RUNNING"
fi

echo ""

# Check if port 8080 is in use
if lsof -i :8080 > /dev/null 2>&1; then
    echo "✅ Port 8080: IN USE"
    lsof -i :8080 | grep LISTEN
else
    echo "❌ Port 8080: NOT IN USE"
fi

echo ""

# Check if .env file exists and has cookie
if [ -f "/workspaces/Dev/need_a_new_job/.env" ]; then
    echo "✅ .env file: EXISTS"
    if grep -q "LINKEDIN_COOKIE=" /workspaces/Dev/need_a_new_job/.env; then
        cookie_length=$(grep "LINKEDIN_COOKIE=" /workspaces/Dev/need_a_new_job/.env | cut -d'=' -f2 | wc -c)
        echo "   Cookie length: $cookie_length characters"
    else
        echo "   ⚠️  Warning: LINKEDIN_COOKIE not found in .env"
    fi
else
    echo "❌ .env file: NOT FOUND"
fi

echo ""

# Try to connect to the server
echo "Testing server connection..."
if timeout 5 curl -s http://localhost:8080/mcp > /dev/null 2>&1; then
    echo "✅ Server Endpoint: REACHABLE at http://localhost:8080/mcp"
else
    echo "❌ Server Endpoint: NOT REACHABLE"
fi

echo ""
echo "=========================================="

# Provide action recommendations
if pgrep -f "linkedin_mcp_server" > /dev/null; then
    echo "Server is running! Use ./add_to_claude.sh to get configuration."
else
    echo "Server is not running. Start it with: ./start_linkedin_mcp.sh"
fi

echo "=========================================="
