# 4. High-Level Architecture

## 4.1 Architecture Style

**Hybrid Architecture:**
- **Event-Driven** (job discovery → queue → workers)
- **Pipeline** (sequential agent processing)
- **Microkernel** (core engine + platform plugins)

## 4.2 System Architecture Diagram

```
┌───────────────────────────────────────────────────────────────────────┐
│                          Gradio UI Layer                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐     │
│  │ Dashboard  │  │  Pipeline  │  │  Pending   │  │  Approval  │     │
│  │   Page     │  │   View     │  │   Jobs     │  │   Queue    │     │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘     │
│        │               │               │               │             │
│        └───────────────┴───────────────┴───────────────┘             │
│                              │                                        │
│                              │ HTTP/WebSocket                         │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│                       FastAPI Application Layer                       │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  API Endpoints                                                  │  │
│  │  - /jobs (list, filter, search)                                │  │
│  │  - /pipeline (current status, WebSocket updates)               │  │
│  │  - /pending (list, retry, skip)                                │  │
│  │  - /approval (list, approve, reject)                           │  │
│  │  - /metrics (dashboard stats)                                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │  Service Layer                                                  │  │
│  │  - JobService (CRUD, state transitions)                        │  │
│  │  - AgentOrchestrator (pipeline execution)                      │  │
│  │  - DuplicateDetectionService (similarity algorithms)           │  │
│  │  - NotificationService (WebSocket broadcasts)                  │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│                      Worker Layer (RQ Workers)                        │
│                                                                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐   │
│  │  Discovery       │  │  Pipeline        │  │  Submission      │   │
│  │  Workers         │  │  Workers         │  │  Workers         │   │
│  │                  │  │                  │  │                  │   │
│  │  - Poll LinkedIn │  │  - Run 7 agents  │  │  - Send email    │   │
│  │  - Scrape SEEK   │  │  - Checkpoint    │  │  - Fill forms    │   │
│  │  - Scrape Indeed │  │  - Error handle  │  │  - Track status  │   │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘   │
│           │                     │                     │              │
│           └─────────────────────┴─────────────────────┘              │
│                              │                                        │
└──────────────────────────────┼────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│                         Queue Layer (Redis)                           │
│                                                                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐      │
│  │ discovery_queue │  │ pipeline_queue  │  │ submission_queue│      │
│  │                 │  │                 │  │                 │      │
│  │  Job discovery  │  │  Agent pipeline │  │  Application    │      │
│  │  tasks          │  │  processing     │  │  submission     │      │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────▼────────────────────────────────────────┐
│                    Data & Storage Layer                               │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │   DuckDB     │  │  File System │  │  MCP Servers             │   │
│  │              │  │              │  │                          │   │
│  │ - jobs       │  │ - CV/CL      │  │ - LinkedIn MCP           │   │
│  │ - tracking   │  │   templates  │  │ - Docker MCP Gateway     │   │
│  │ - metrics    │  │ - Generated  │  │   (browser, knowledge    │   │
│  │              │  │   documents  │  │    graph, Obsidian)      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---
