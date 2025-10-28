# 9. Risks & Mitigations

## 9.1 Technical Risks

**Risk:** LinkedIn/SEEK/Indeed block automation (ToS violation)
- **Likelihood:** Medium
- **Impact:** High (core functionality broken)
- **Mitigation:**
  - Implement rate limiting
  - Use realistic user-agent headers
  - Add random delays between requests
  - Fallback: Manual job URL input mode

**Risk:** LinkedIn cookie expires frequently
- **Likelihood:** High (every ~30 days)
- **Impact:** Medium (LinkedIn jobs not discovered)
- **Mitigation:**
  - Alert user when cookie expires (UI notification)
  - Document cookie refresh process
  - Consider OAuth flow (V2)

**Risk:** Claude API rate limits or costs
- **Likelihood:** Medium
- **Impact:** Medium (agent processing slows/stops)
- **Mitigation:**
  - Implement exponential backoff
  - Queue jobs during rate limit window
  - Monitor API costs (budget alerts)
  - Use cheaper models (Haiku) for simple agents

**Risk:** Complex web forms cannot be automated
- **Likelihood:** High
- **Impact:** Medium (some jobs require manual submission)
- **Mitigation:**
  - Mark as `pending` for manual intervention
  - Build form-specific plugins over time (V2)
  - Accept 50% automation rate as MVP success

## 9.2 Quality Risks

**Risk:** Agent fabricates information in CV/CL
- **Likelihood:** Low (with QA agent)
- **Impact:** Critical (damages reputation)
- **Mitigation:**
  - QA agent validates factual accuracy
  - Approval mode for user review
  - Log all agent outputs for audit

**Risk:** Duplicate applications sent to same company
- **Likelihood:** Low (with deduplication)
- **Impact:** High (unprofessional)
- **Mitigation:**
  - Robust 2-tier similarity algorithm
  - Manual review for 75-89% similarity scores
  - Track all submissions in database

**Risk:** Australian English violations
- **Likelihood:** Low (with QA agent)
- **Impact:** Medium (looks unprofessional)
- **Mitigation:**
  - QA agent checks spelling/grammar
  - Approval mode for user review
  - Build Australian English dictionary

## 9.3 Operational Risks

**Risk:** System crashes during continuous monitoring
- **Likelihood:** Medium
- **Impact:** Medium (jobs missed during downtime)
- **Mitigation:**
  - Auto-restart on failure (systemd, Docker)
  - Health check endpoint
  - Alerting on downtime

**Risk:** Disk space fills with CV/CL files
- **Likelihood:** Medium (after months of operation)
- **Impact:** Low (easily resolved)
- **Mitigation:**
  - Archive old applications (>3 months)
  - Monitor disk usage
  - Compress archived files

---
