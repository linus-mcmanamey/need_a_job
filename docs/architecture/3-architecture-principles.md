# 3. Architecture Principles

## 3.1 Design Principles

1. **Separation of Concerns**
   - Each agent has single responsibility
   - Platform pollers decoupled from processing
   - UI separated from business logic

2. **Fail-Safe with Checkpoints**
   - Every agent saves output before proceeding
   - Failed jobs resume from last successful agent
   - No data loss on errors

3. **Human-in-the-Loop**
   - Approval mode for quality control
   - Pending jobs for manual intervention
   - Dry-run mode for testing

4. **Local-First, Privacy-Conscious**
   - All personal data stored locally
   - No cloud storage of CVs/cover letters
   - Credentials in local `.env` only

5. **Extensibility**
   - Easy to add new job platforms (YAML config or Python plugin)
   - Agent system allows new agents to be inserted
   - Configuration-driven behavior

6. **Observability**
   - Every action logged
   - Real-time UI updates
   - Agent performance metrics tracked

## 3.2 Technology Principles

1. **Python-First:** Leverage existing Python expertise
2. **Minimal JavaScript:** Use Gradio to avoid frontend complexity
3. **Proven Technologies:** FastAPI, Redis, DuckDB (mature, stable)
4. **MCP Integration:** Leverage Model Context Protocol for LLM tooling
5. **Open Source:** Prefer OSS libraries and tools

---
