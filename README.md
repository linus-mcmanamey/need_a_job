# LinkedIn MCP Server Setup

This repository contains a LinkedIn MCP (Model Context Protocol) server setup that allows Claude Code to interact with your LinkedIn account.

## Prerequisites

- Python 3.12+
- uv package manager
- Chrome browser (for local development)
- LinkedIn account with valid cookie

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root with your LinkedIn cookie:

```bash
LINKEDIN_COOKIE=li_at=YOUR_LINKEDIN_COOKIE_VALUE
```

**How to get your LinkedIn cookie:**
1. Open LinkedIn in Chrome and log in
2. Open Chrome DevTools (F12 or right-click → Inspect)
3. Go to **Application** tab → **Storage** → **Cookies** → **https://www.linkedin.com**
4. Find the cookie named `li_at`
5. Copy the **Value** field

### 2. Installation

Run the installation script:

```bash
bash linkedin_mcp.sh
```

This will:
- Clone the linkedin-mcp-server repository
- Install uv package manager
- Install Python dependencies
- Set up pre-commit hooks
- Start the MCP server using your `.env` cookie

### 3. Start the Server

#### Option A: Using the startup script (Recommended)

```bash
./start_linkedin_mcp.sh
```

This script:
- Loads the LinkedIn cookie from `.env` file
- Starts the MCP server in HTTP mode
- Makes it available at `http://0.0.0.0:8080/mcp`

#### Option B: Manual start

```bash
cd linkedin-mcp-server
source .venv/bin/activate
export $(grep -v '^#' ../.env | grep LINKEDIN_COOKIE | xargs)
python -m linkedin_mcp_server --cookie "$LINKEDIN_COOKIE" --transport streamable-http --host 0.0.0.0 --port 8080 --path /mcp
```

## Claude Code Integration

### Method 1: Using MCP Configuration File

The `mcp_config.json` file contains the configuration for Claude Code:

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

To add to Claude Code, you can manually merge this into your Claude Code MCP configuration.

### Method 2: Manual Configuration

Add this to your Claude Code MCP settings:

```json
{
  "mcpServers": {
    "linkedin": {
      "command": "/workspaces/Dev/need_a_new_job/linkedin-mcp-server/.venv/bin/python",
      "args": [
        "-m",
        "linkedin_mcp_server",
        "--cookie",
        "YOUR_LINKEDIN_COOKIE_HERE"
      ]
    }
  }
}
```

**Note:** Replace `YOUR_LINKEDIN_COOKIE_HERE` with the actual cookie value from your `.env` file.

## Available Tools

Once connected, Claude can use these LinkedIn tools:

- **get_person_profile**: Get detailed profile information from a LinkedIn profile URL
- **get_company_profile**: Extract company information from a LinkedIn company page
- **get_job_details**: Retrieve job posting details using LinkedIn job IDs
- **search_jobs**: Search for jobs with filters like keywords and location
- **get_recommended_jobs**: Get personalized job recommendations
- **close_session**: Close browser session and clean up resources

## Usage Examples

Ask Claude:
```
What are my recommended jobs I can apply to?
```

```
Research the background of this candidate https://www.linkedin.com/in/username/
```

```
Get this company profile https://www.linkedin.com/company/company-name/
```

```
Suggest improvements for my CV to target this job posting https://www.linkedin.com/jobs/view/1234567890
```

## File Structure

```
.
├── .env                        # LinkedIn cookie (gitignored)
├── linkedin_mcp.sh            # Installation and setup script
├── start_linkedin_mcp.sh      # Server startup script
├── mcp_config.json            # MCP configuration for Claude Code
├── README.md                  # This file
└── linkedin-mcp-server/       # MCP server repository (cloned)
    ├── .venv/                 # Python virtual environment
    └── linkedin_mcp_server/   # Server source code
```

## Troubleshooting

### Server won't start
- Check that your `.env` file exists and contains a valid `LINKEDIN_COOKIE`
- Verify the cookie hasn't expired (LinkedIn cookies expire after ~30 days)
- Make sure no other process is using port 8080

### Cookie expired
1. Get a new cookie from LinkedIn (see step 1 above)
2. Update your `.env` file
3. Restart the server

### Keyring errors
These are warnings and can be ignored. The server will use the cookie from the `.env` file instead of the system keychain.

### Connection issues
- Ensure the server is running: `ps aux | grep linkedin_mcp_server`
- Check the server logs in the terminal where you started it
- Verify port 8080 is accessible: `curl http://localhost:8080/mcp`

## Security Notes

- **Never commit your `.env` file** - it contains your LinkedIn session cookie
- The `.env` file is already in `.gitignore`
- LinkedIn cookies expire after ~30 days
- Only use this for personal, non-commercial purposes
- Be aware that web scraping may violate LinkedIn's Terms of Service

## License

This project uses the [LinkedIn MCP Server](https://github.com/stickerdaniel/linkedin-mcp-server) which is licensed under Apache 2.0.
