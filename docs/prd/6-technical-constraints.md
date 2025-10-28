# 6. Technical Constraints

## 6.1 Technology Stack

- **Language:** Python 3.11+ (user has advanced experience)
- **Backend Framework:** FastAPI
- **Task Queue:** Redis + RQ (background job processing)
- **Database:** DuckDB (embedded, local)
- **UI Framework:** Gradio (pure Python)
- **LLM:** Claude (multiple models: Haiku, Sonnet, Opus)
- **MCP Integration:** LinkedIn MCP, Docker MCP Gateway (browser, knowledge graph, Obsidian)
- **Browser Automation:** Playwright or Chrome MCP
- **Document Processing:** python-docx (for .docx CV/CL)

## 6.2 External Dependencies

- **LinkedIn MCP Server:** Requires valid `li_at` cookie (expires ~30 days)
- **Redis Server:** Must be running for task queue
- **Docker:** Required for Docker MCP Gateway
- **Internet Connection:** Required for job discovery and LLM API calls

## 6.3 File System

- **CV/CL Templates:** `current_cv_coverletter/` (gitignored)
- **Generated Applications:** `export_cv_cover_letter/YYYY-MM-DD_company_title/` (gitignored)
- **Configuration Files:** `search.yaml`, `agents.yaml`, `platforms.yaml` (committed to repo)
- **Database:** `job_applications.duckdb` (gitignored)

---
