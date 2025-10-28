# 12. Technology Stack

## 12.1 Core Technologies

| Component | Technology | Version | Justification |
|-----------|-----------|---------|---------------|
| Language | Python | 3.11+ | User expertise, MCP support, rich ecosystem |
| Web Framework | FastAPI | 0.100+ | Modern, async, auto-docs, WebSocket support |
| Task Queue | Redis + RQ | Redis 7, RQ 1.15+ | Simple Python integration, reliable |
| Database | DuckDB | 0.9+ | Embedded, fast analytics, SQL support |
| UI Framework | Gradio | 4.0+ | Pure Python, quick dashboards, real-time updates |
| LLM | Claude | Opus/Sonnet/Haiku | State-of-art reasoning, multiple models for cost optimization |
| MCP | LinkedIn MCP, Docker MCP | Latest | Seamless LLM tool integration |
| Browser Automation | Playwright or Chrome MCP | Latest | Web form automation, reliable |
| Document Processing | python-docx | 0.8+ | Read/write .docx files |

## 12.2 Development Tools

- **Version Control:** Git + GitHub
- **Linting:** ruff (fast Python linter)
- **Formatting:** black (code formatter)
- **Type Checking:** mypy (static type checking)
- **Testing:** pytest (unit/integration tests)
- **Documentation:** mkdocs (if needed for V2)

## 12.3 Dependencies

```toml
# pyproject.toml
[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.100.0"
uvicorn = "^0.23.0"
redis = "^5.0.0"
rq = "^1.15.0"
duckdb = "^0.9.0"
gradio = "^4.0.0"
anthropic = "^0.18.0"
playwright = "^1.40.0"
python-docx = "^0.8.11"
pydantic = "^2.0.0"
pyyaml = "^6.0"
python-dotenv = "^1.0.0"
loguru = "^0.7.0"

[tool.poetry.dev-dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"
black = "^23.0.0"
ruff = "^0.1.0"
mypy = "^1.5.0"
```

---
