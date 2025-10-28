# 9. Deployment Architecture

## 9.1 Development Environment

```yaml
# docker-compose.yml (for local development)
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  app:
    build: .
    ports:
      - "8000:8000"  # FastAPI
      - "7860:7860"  # Gradio
    environment:
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - SMTP_SERVER=${SMTP_SERVER}
      - SMTP_PORT=${SMTP_PORT}
      - SENDER_EMAIL=${SENDER_EMAIL}
      - SENDER_PASSWORD=${SENDER_PASSWORD}
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./current_cv_coverletter:/app/current_cv_coverletter
      - ./export_cv_cover_letter:/app/export_cv_cover_letter
    depends_on:
      - redis

  worker:
    build: .
    command: rq worker --url redis://redis:6379
    environment:
      - REDIS_URL=redis://redis:6379
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./config:/app/config
      - ./data:/app/data
      - ./current_cv_coverletter:/app/current_cv_coverletter
      - ./export_cv_cover_letter:/app/export_cv_cover_letter
    depends_on:
      - redis
    deploy:
      replicas: 3  # Multiple workers for parallel processing

volumes:
  redis_data:
```

## 9.2 Process Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Host Machine                             │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Docker Compose Stack                                │   │
│  │                                                      │   │
│  │  ┌────────────────┐                                 │   │
│  │  │ Redis          │                                 │   │
│  │  │ (Queue + Cache)│                                 │   │
│  │  └───────┬────────┘                                 │   │
│  │          │                                          │   │
│  │  ┌───────┴─────────────────────────────────────┐   │   │
│  │  │                                             │   │   │
│  │  │  ┌──────────────┐  ┌──────────────┐       │   │   │
│  │  │  │ FastAPI App  │  │ Gradio UI    │       │   │   │
│  │  │  │ (Port 8000)  │  │ (Port 7860)  │       │   │   │
│  │  │  └──────────────┘  └──────────────┘       │   │   │
│  │  │                                             │   │   │
│  │  │  ┌──────────────┐  ┌──────────────┐       │   │   │
│  │  │  │ RQ Worker 1  │  │ RQ Worker 2  │  ...  │   │   │
│  │  │  │ (Discovery)  │  │ (Pipeline)   │       │   │   │
│  │  │  └──────────────┘  └──────────────┘       │   │   │
│  │  │                                             │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  File System (Volumes)                               │   │
│  │  - config/                                           │   │
│  │  - data/job_applications.duckdb                      │   │
│  │  - current_cv_coverletter/                           │   │
│  │  - export_cv_cover_letter/                           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 9.3 Running the System

```bash
# Start all services
docker-compose up -d

# Access Gradio UI
open http://localhost:7860

# View logs
docker-compose logs -f worker

# Scale workers
docker-compose up -d --scale worker=5

# Stop system
docker-compose down
```

**Alternative: Non-Docker Development**

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start FastAPI
uvicorn app.main:app --reload

# Terminal 3: Start RQ workers
rq worker --burst  # Or run continuously

# Terminal 4: Start Gradio UI
python app/ui/gradio_app.py
```

---
