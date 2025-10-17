# 1. Clone repository
git clone https://github.com/stickerdaniel/linkedin-mcp-server
cd linkedin-mcp-server

# 2. Install UV package manager
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python # install python if you don't have it

# 3. Install dependencies and dev dependencies
uv sync
uv sync --group dev

# 4. Install pre-commit hooks
uv run pre-commit install

# 5. Load LinkedIn cookie from .env file and start server
# Make sure you have a .env file in the parent directory with LINKEDIN_COOKIE set
cd ..
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | grep LINKEDIN_COOKIE | xargs)
    if [ -n "$LINKEDIN_COOKIE" ]; then
        echo "LinkedIn cookie loaded from .env file"
        cd linkedin-mcp-server
        .venv/bin/python -m linkedin_mcp_server --cookie "$LINKEDIN_COOKIE" --transport streamable-http --host 0.0.0.0 --port 8080 --path /mcp --log-level INFO
    else
        echo "Error: LINKEDIN_COOKIE not found in .env file"
        exit 1
    fi
else
    echo "Error: .env file not found in parent directory"
    echo "Please create a .env file with LINKEDIN_COOKIE=your_cookie_value"
    exit 1
fi