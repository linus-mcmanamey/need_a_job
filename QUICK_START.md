# LinkedIn MCP Server - Quick Start Guide

## Current Status ✅

The LinkedIn MCP Server is **installed, running, and connected to Claude Code**!

- **Server Status**: ✓ Connected
- **Authentication**: Using cookie from `.env` file
- **Version**: v1.4.0
- **Registration**: Added to Claude Code via `run_linkedin_mcp.sh` wrapper

## What You Can Do Now

### 1. View Your Configuration

Run this command to see all three methods to connect Claude Code:

```bash
./add_to_claude.sh
```

### 2. Add to Claude Code

Choose one of these methods:

#### Method 1: stdio (Recommended)
```json
{
  "mcpServers": {
    "linkedin": {
      "command": "bash",
      "args": [
        "-c",
        "export $(grep -v '^#' /workspaces/Dev/need_a_new_job/.env | grep LINKEDIN_COOKIE | xargs) && /workspaces/Dev/need_a_new_job/linkedin-mcp-server/.venv/bin/python -m linkedin_mcp_server --cookie \"$LINKEDIN_COOKIE\""
      ]
    }
  }
}
```

#### Method 2: Direct Python (Alternative)
```json
{
  "mcpServers": {
    "linkedin": {
      "command": "/workspaces/Dev/need_a_new_job/linkedin-mcp-server/.venv/bin/python",
      "args": [
        "-m",
        "linkedin_mcp_server",
        "--cookie",
        "YOUR_COOKIE_FROM_ENV_FILE"
      ]
    }
  }
}
```

#### Method 3: HTTP Server (For Testing)
The server is already running! Just connect to:
```json
{
  "mcpServers": {
    "linkedin": {
      "url": "http://localhost:8080/mcp",
      "transport": "streamable-http"
    }
  }
}
```

## Available LinkedIn Tools

Once connected, ask Claude to:

1. **Get Job Recommendations**
   ```
   What are my recommended jobs I can apply to?
   ```

2. **Research Profiles**
   ```
   Research the background of this candidate https://www.linkedin.com/in/username/
   ```

3. **Company Analysis**
   ```
   Get company profile https://www.linkedin.com/company/company-name/
   ```

4. **Job Details**
   ```
   Analyze this job posting https://www.linkedin.com/jobs/view/1234567890
   ```

5. **Search Jobs**
   ```
   Search for Python developer jobs in San Francisco
   ```

## Server Management

### Start the Server
```bash
./start_linkedin_mcp.sh
```

### Stop the Server
Find the process and kill it:
```bash
ps aux | grep linkedin_mcp_server
kill <PID>
```

Or use Ctrl+C if running in foreground.

### View Server Logs
The server outputs logs to stderr. Check the terminal where you started it.

### Restart the Server
```bash
# Kill existing process
pkill -f linkedin_mcp_server

# Start again
./start_linkedin_mcp.sh
```

## File Structure

```
/workspaces/Dev/need_a_new_job/
├── .env                        # Your LinkedIn cookie (secret!)
├── .gitignore                  # Prevents .env from being committed
├── linkedin_mcp.sh            # Initial setup script
├── start_linkedin_mcp.sh      # Server startup script
├── add_to_claude.sh           # Shows Claude Code config
├── mcp_config.json            # MCP configuration template
├── README.md                  # Full documentation
├── QUICK_START.md             # This file
└── linkedin-mcp-server/       # MCP server (cloned from GitHub)
    └── .venv/                 # Python virtual environment
```

## Troubleshooting

### Cookie Expired?
1. Get new cookie from LinkedIn (see README.md)
2. Update `.env` file
3. Restart server: `./start_linkedin_mcp.sh`

### Server Not Responding?
```bash
# Check if running
ps aux | grep linkedin_mcp_server

# Check port
lsof -i :8080

# View logs
./start_linkedin_mcp.sh  # Run in foreground to see logs
```

### Claude Code Can't Connect?
1. Verify server is running on port 8080
2. Check your MCP configuration syntax
3. Restart Claude Code after adding configuration
4. Try Method 3 (HTTP) first for testing

## Security Reminder

- Never commit `.env` file (it's in `.gitignore`)
- LinkedIn cookie expires in ~30 days
- Don't share your cookie with others
- Use for personal purposes only

## Next Steps

1. Run `./add_to_claude.sh` to see your configuration options
2. Copy one of the configurations
3. Add it to Claude Code MCP settings
4. Restart Claude Code
5. Ask Claude to use LinkedIn tools!

---

**Need Help?** Check [README.md](README.md) for full documentation.
