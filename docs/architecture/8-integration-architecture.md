# 8. Integration Architecture

## 8.1 MCP Integration

**Model Context Protocol (MCP) Servers:**

```python
class MCPClientManager:
    def __init__(self, mcp_config_path='.mcp.json'):
        self.config = self.load_config(mcp_config_path)
        self.clients = {}

        for server_name, server_config in self.config['mcpServers'].items():
            self.clients[server_name] = MCPClient(server_config)

    def get_linkedin_client(self) -> LinkedInMCP:
        return self.clients['linkedin']

    def get_docker_mcp_client(self) -> DockerMCP:
        return self.clients['MCP_DOCKER']

# Usage in pollers
class LinkedInPoller:
    def __init__(self):
        mcp_manager = MCPClientManager()
        self.linkedin = mcp_manager.get_linkedin_client()

    def poll(self):
        return self.linkedin.search_jobs(
            keywords="data engineer contract",
            location="Australia"
        )

class SeekPoller:
    def __init__(self):
        mcp_manager = MCPClientManager()
        self.browser = mcp_manager.get_docker_mcp_client().browser

    def poll(self):
        self.browser.navigate("https://www.seek.com.au/data-engineer-jobs")
        return self.browser.extract_job_listings()
```

**MCP Tools Used:**
- **LinkedIn MCP:** `search_jobs`, `get_job_details`, `get_company_profile`
- **Docker MCP Gateway:**
  - Browser: `browser_navigate`, `browser_snapshot`, `browser_take_screenshot`
  - Knowledge Graph: `create_entities`, `create_relations` (for tracking job relationships)
  - Obsidian: `obsidian_append_content` (for job notes)

## 8.2 External API Integration

```python
class ClaudeClient:
    """Wrapper for Claude API with retry and caching"""
    def __init__(self, model='claude-sonnet-4'):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        self.model = model
        self.client = anthropic.Client(api_key=self.api_key)

    @retry(tries=3, delay=2, backoff=2)
    def complete(self, prompt: str, system: str = None) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def embed(self, text: str) -> List[float]:
        # Use Claude embedding endpoint (if available) or fallback
        # For MVP, may use TF-IDF instead of embeddings (cheaper)
        pass

class EmailService:
    """Email sending service"""
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.email = os.getenv('SENDER_EMAIL')
        self.password = os.getenv('SENDER_PASSWORD')

    def send(self, to: str, subject: str, body: str, attachments: List[str]):
        msg = MIMEMultipart()
        msg['From'] = self.email
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        for filepath in attachments:
            with open(filepath, 'rb') as f:
                part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
                msg.attach(part)

        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email, self.password)
            server.send_message(msg)
```

---
