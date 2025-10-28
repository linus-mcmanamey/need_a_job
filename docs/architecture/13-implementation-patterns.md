# 13. Implementation Patterns

## 13.1 Design Patterns Used

1. **Strategy Pattern** (Platform Pollers)
   - Interchangeable poller implementations
   - Easy to add new platforms

2. **Chain of Responsibility** (Agent Pipeline)
   - Sequential processing through agents
   - Each agent decides to continue or stop

3. **Command Pattern** (RQ Jobs)
   - Jobs encapsulate actions (poll, process, submit)
   - Queueable, retriable, cancellable

4. **Repository Pattern** (Database Access)
   - Abstraction over DuckDB queries
   - Easy to swap database later

5. **Dependency Injection** (Services, Agents)
   - Pass dependencies (DB, MCP clients) to constructors
   - Easier testing with mocks

## 13.2 Error Handling Pattern

```python
class JobProcessor:
    def process_job(self, job_id: str):
        try:
            # Attempt processing
            self.orchestrator.process_job(job_id)
        except AgentExecutionError as e:
            # Agent failed, checkpoint saved by orchestrator
            self.notification_service.notify_error(job_id, e)
            # Job marked as 'pending', can be retried
        except ExternalServiceError as e:
            # External service (Claude API, LinkedIn) failed
            self.retry_later(job_id, delay=300)  # Retry in 5 minutes
        except Exception as e:
            # Unexpected error
            self.logger.error(f"Unexpected error processing {job_id}: {e}")
            self.mark_as_failed(job_id, e)
```

## 13.3 Configuration Pattern

```python
class Config:
    """Singleton config loader"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.load_all()
        return cls._instance

    def load_all(self):
        self.search = self.load_yaml('config/search.yaml')
        self.agents = self.load_yaml('config/agents.yaml')
        self.platforms = self.load_yaml('config/platforms.yaml')

    def load_yaml(self, path):
        with open(path) as f:
            return yaml.safe_load(f)

# Usage
config = Config()
keywords = config.search['keywords']['primary']
match_threshold = config.agents['job_matcher_agent']['match_threshold']
```

---
