# 5. Non-Functional Requirements

## 5.1 Performance

- **Job Discovery Latency:** New jobs detected within 1 hour of posting
- **Agent Pipeline Throughput:** Process 1 job in <5 minutes (end-to-end)
- **UI Responsiveness:** Dashboard updates within 2 seconds
- **Database Queries:** All queries complete in <1 second

## 5.2 Reliability

- **Uptime Target:** 95%+ (continuous monitoring, auto-restart on failure)
- **Error Recovery:** All agent failures logged, jobs marked `pending` with checkpoint
- **Data Integrity:** No duplicate applications to same job (deduplication)
- **Factual Accuracy:** 100% - no fabricated information in CVs/CLs

## 5.3 Security & Privacy

- **Credential Management:** LinkedIn cookies, email credentials in `.env` (gitignored)
- **Personal Data:** CV/CL templates gitignored, never committed to repo
- **Application Data:** All generated CVs/CLs stored locally, not in cloud
- **API Keys:** Claude API keys in `.env`, rate-limited

## 5.4 Compliance

- **Platform Terms of Service:** Acknowledge SEEK/Indeed/LinkedIn ToS restrictions on automation
  - Rate limiting enforced
  - User-agent headers identify bot
  - Respect robots.txt
- **Australian English Standards:** All output uses Australian spelling, date formats, terminology
- **Employment Law:** No discriminatory filtering, all applications fact-based

## 5.5 Usability

- **Setup Time:** <30 minutes from clone to first job discovered
- **Learning Curve:** New user can understand dashboard in <10 minutes
- **Manual Intervention Rate (MVP):** <50% of jobs require manual review
- **Manual Intervention Rate (V2):** <10% of jobs require manual review

---
