# 10. Security Architecture

## 10.1 Credential Management

```bash
# .env file (gitignored)
ANTHROPIC_API_KEY=sk-ant-...
LINKEDIN_LI_AT_COOKIE=AQEDATc...
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your.email@gmail.com
SENDER_PASSWORD=your_app_password
REDIS_URL=redis://localhost:6379
```

**Security Measures:**
- All credentials in `.env` (never committed)
- Docker secrets for production (if deployed)
- LinkedIn cookie expires ~30 days (manual refresh)
- Email uses app-specific password (not main password)

## 10.2 Data Privacy

- **Personal Documents:** CV/CL templates gitignored, stored locally only
- **Generated Applications:** All in gitignored directories, never cloud-synced
- **Database:** DuckDB file local, contains no credentials
- **Logs:** Sanitize sensitive data (redact emails, company names if needed)

## 10.3 API Rate Limiting

```python
class RateLimiter:
    def __init__(self, calls_per_hour):
        self.calls_per_hour = calls_per_hour
        self.calls = deque()

    def acquire(self):
        now = time.time()
        # Remove calls older than 1 hour
        while self.calls and self.calls[0] < now - 3600:
            self.calls.popleft()

        if len(self.calls) >= self.calls_per_hour:
            sleep_time = 3600 - (now - self.calls[0])
            time.sleep(sleep_time)

        self.calls.append(now)

# Usage
linkedin_limiter = RateLimiter(calls_per_hour=100)
seek_limiter = RateLimiter(calls_per_hour=50)

def poll_linkedin():
    linkedin_limiter.acquire()
    # Make API call
```

---
