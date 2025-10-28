# 1. Executive Summary

This document describes the system architecture for an automated job application system built with Python, FastAPI, Gradio, Redis, DuckDB, and Claude LLM. The system uses a **multi-agent pipeline architecture** with **event-driven job discovery**, **checkpoint-based error recovery**, and **human-in-the-loop controls**.

**Key Architectural Decisions:**
- **Multi-agent pipeline:** Specialized agents process jobs sequentially with approval gates
- **Event-driven discovery:** Platform pollers push jobs to central queue, workers consume
- **Checkpoint system:** Agent progress saved for resume-on-failure
- **Hybrid duplicate detection:** Fast fuzzy matching + deep LLM embedding analysis
- **Gradio UI:** Pure Python interface with WebSocket real-time updates
- **Local-first:** All data stored locally (DuckDB, filesystem), no cloud dependencies

---
