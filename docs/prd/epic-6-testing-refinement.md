# Epic 6: Testing & Refinement (Weeks 6-7)

**Epic Goal:** Comprehensive testing, error handling improvements, performance optimization, and production readiness.

**Epic Value:** Ensures the system is reliable, performant, and ready for real-world use.

**Timeline:** Weeks 6-7

**Deliverable:** MVP COMPLETE - Production-ready system

---

## Story 6.1: End-to-End Integration Testing

**As a** developer
**I want to** test the complete job pipeline from discovery to submission
**So that** I can verify all components work together correctly

### Acceptance Criteria:
1. Integration test suite created with test scenarios:
   - **Scenario 1:** New job discovered → matched → documents generated → submitted via email
   - **Scenario 2:** Job discovered → rejected by Job Matcher (low score)
   - **Scenario 3:** Job discovered → documents generated → complex form detected → marked pending
   - **Scenario 4:** Duplicate job detected → grouped with existing job → applied to all platforms
   - **Scenario 5:** Agent failure → checkpoint saved → resumed successfully
2. Test data setup:
   - Mock LinkedIn/SEEK/Indeed job listings (realistic data)
   - Mock email server for submission testing (use mailtrap.io or similar)
   - Test DOCX templates (CV and CL)
   - Configuration files for testing
3. Test execution framework:
   - Automated test runner (pytest)
   - Test database (separate from production)
   - Clean database state before each test
4. Assertions for each scenario:
   - Database state (jobs, application_tracking)
   - Generated files (CV, CL exist and valid)
   - Agent outputs (match scores, decisions)
   - Status transitions correct
5. Test coverage:
   - All 7 agents tested individually (unit tests)
   - Agent pipeline tested as whole (integration tests)
   - Database operations tested (CRUD, queries)
   - Configuration loading tested
6. CI/CD integration:
   - Tests run automatically on commit (GitHub Actions)
   - Test results reported in PR comments
   - Build fails if tests fail

### Technical Notes:
- Use pytest for test framework
- Use pytest-mock for mocking external APIs (Claude, LinkedIn MCP)
- Use pytest-asyncio for async tests
- Test database: In-memory DuckDB or separate file
- Aim for 80%+ code coverage

---

## Story 6.2: Error Handling and Resilience

**As a** system
**I want to** handle errors gracefully and recover automatically
**So that** transient failures don't require manual intervention

### Acceptance Criteria:
1. Retry logic implemented for common failures:
   - **API timeouts:** Retry 3 times with exponential backoff (2s, 4s, 8s)
   - **Rate limiting:** Wait for rate limit reset, then retry
   - **Network errors:** Retry 3 times with backoff
   - **File I/O errors:** Retry once, log error details
2. Error classification:
   - **Transient errors:** Can be retried (network, timeout, rate limit)
   - **Permanent errors:** Can't be retried (invalid data, authentication failure)
   - Mark jobs with permanent errors as "failed" immediately
3. Circuit breaker pattern for external services:
   - After 5 consecutive failures, open circuit
   - Don't make requests for 5 minutes
   - Try again after cooldown period
   - Close circuit after 3 consecutive successes
4. Database transaction handling:
   - All database updates wrapped in transactions
   - Rollback on error
   - Atomic operations (no partial updates)
5. Logging improvements:
   - Structured logging (JSON format)
   - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
   - Include context: job_id, agent_name, timestamp
   - Log aggregation (optional: send to CloudWatch or Datadog)
6. Error notifications:
   - Critical errors trigger alerts (email or Slack)
   - Weekly error summary report
7. Graceful degradation:
   - If Claude API unavailable, mark jobs as pending (don't fail entire pipeline)
   - If Redis unavailable, use in-memory queue (fallback)
   - If Playwright unavailable, mark web form jobs as pending

### Technical Notes:
- Use tenacity library for retry logic
- Circuit breaker: pybreaker library
- Structured logging: structlog library
- Error monitoring: Sentry integration (optional)
- Alerting: Use existing notification channels (email/Slack from Epic 5)

---

## Story 6.3: Resume from Checkpoint Testing

**As a** developer
**I want to** verify that failed jobs can resume from checkpoints correctly
**So that** I can trust the system to recover from errors

### Acceptance Criteria:
1. Test checkpoint save functionality:
   - Simulate agent failures at each stage
   - Verify checkpoint data saved correctly
   - Verify database state consistent
2. Test checkpoint resume functionality:
   - Resume job from each possible failure point
   - Verify correct agent is executed next
   - Verify completed agents are skipped
   - Verify agent outputs preserved
3. Test scenarios:
   - **Job Matcher fails:** Resume from Job Matcher
   - **CV Tailor fails:** Resume from CV Tailor (keep Matcher output)
   - **QA fails:** Resume from QA (keep Matcher, Salary, CV, CL outputs)
   - **Application Handler fails:** Resume from Application Handler
4. Overwrite behavior tested:
   - On successful retry, verify failed attempt overwritten
   - error_info cleared
   - Status updated correctly
5. Multiple retry attempts:
   - Test max retry limit (3 attempts)
   - Verify job marked as permanently failed after max retries
6. Edge cases:
   - Resume job that was never started (error before first agent)
   - Resume job with corrupted checkpoint data
   - Resume job after system restart

### Technical Notes:
- Use pytest fixtures for test setup
- Mock agent failures with exceptions
- Test with different error types (API, validation, file I/O)
- Verify checkpoint data structure (JSON schema validation)

---

## Story 6.4: Performance Optimization

**As a** system
**I want to** process jobs quickly and efficiently
**So that** applications are submitted promptly after jobs are discovered

### Acceptance Criteria:
1. Job processing throughput:
   - Target: 10 jobs per minute (single worker)
   - Target: 50 jobs per minute (5 workers)
2. Agent execution time optimization:
   - **Job Matcher:** < 5 seconds (use Claude Haiku if faster)
   - **Salary Validator:** < 2 seconds
   - **CV Tailor:** < 15 seconds
   - **Cover Letter Writer:** < 15 seconds
   - **QA:** < 10 seconds
   - **Orchestrator:** < 5 seconds
   - **Application Handler:** < 30 seconds (email), < 60 seconds (web form)
3. Database query optimization:
   - Add indexes for slow queries
   - Use query caching for frequently accessed data
   - Optimize duplicate detection queries (most expensive operation)
4. Parallel processing:
   - Multiple RQ workers running concurrently (5 workers recommended)
   - Jobs distributed evenly across workers
5. Memory optimization:
   - Job descriptions stored efficiently (compress long text)
   - Embeddings cached to avoid regeneration
   - DuckDB query results not held in memory unnecessarily
6. Network optimization:
   - Batch API requests where possible (embeddings)
   - Connection pooling for database and Redis
   - Reuse HTTP sessions for web scraping
7. Performance monitoring:
   - Track agent execution times (percentiles: p50, p90, p99)
   - Track queue depth over time
   - Track database query times
   - Alert if processing rate drops below threshold

### Technical Notes:
- Use cProfile or py-spy for profiling
- Use DuckDB EXPLAIN ANALYZE for query optimization
- Consider using asyncio for concurrent agent execution (future enhancement)
- Monitor Redis memory usage (set maxmemory policy)

---

## Story 6.5: Documentation and Setup Guide

**As a** user or developer
**I want to** comprehensive documentation
**So that** I can set up, configure, and maintain the system

### Acceptance Criteria:
1. README.md includes:
   - Project overview and features
   - System requirements (Python version, dependencies)
   - Quick start guide (5 steps to run locally)
   - Architecture diagram (high-level)
   - Links to detailed documentation
2. SETUP.md includes:
   - Detailed installation instructions
   - Environment variable configuration
   - Database initialization steps
   - Configuration file setup (search.yaml, agents.yaml, etc.)
   - LinkedIn MCP server setup
   - Email account configuration
   - Playwright/Chrome MCP setup
3. CONFIGURATION.md includes:
   - All configuration options explained
   - Default values and recommended settings
   - Examples for different use cases (aggressive, conservative, balanced)
4. ARCHITECTURE.md includes:
   - System architecture diagram
   - Component descriptions (pollers, agents, queue, database)
   - Data flow diagrams
   - Database schema with entity relationship diagram
5. AGENT_GUIDE.md includes:
   - Explanation of each agent's purpose
   - Agent configuration options
   - Prompt engineering guidance
   - Troubleshooting common agent issues
6. USER_GUIDE.md includes:
   - How to use the Gradio UI
   - How to handle pending jobs
   - How to use approval mode
   - How to use dry-run mode
   - How to search application history
7. TROUBLESHOOTING.md includes:
   - Common issues and solutions
   - Error messages explained
   - How to read logs
   - How to reset the system
8. Code documentation:
   - Docstrings for all public functions and classes
   - Type hints throughout codebase
   - Inline comments for complex logic

### Technical Notes:
- Use Markdown for all documentation
- Include code examples and screenshots
- Keep documentation in sync with code (review on each release)
- Consider using MkDocs or Sphinx for documentation site (optional)

---

## Story 6.6: Real-World Testing and Bug Fixes

**As a** developer
**I want to** test the system with real job searches
**So that** I can identify and fix issues before production use

### Acceptance Criteria:
1. Real-world test plan:
   - Run system in dry-run mode for 7 days
   - Monitor 50-100 real job postings
   - Review generated CVs and CLs for quality
   - Check duplicate detection accuracy
   - Verify agent decisions are reasonable
2. Test results documented:
   - Number of jobs discovered per platform
   - Match rates (% of jobs approved by Job Matcher)
   - Duplicate detection accuracy (manual review of 20 duplicate groups)
   - CV/CL quality score (manual review of 10 applications)
   - False positive rate (jobs incorrectly approved)
   - False negative rate (good jobs incorrectly rejected)
3. Bug tracking:
   - All bugs logged in issue tracker (GitHub Issues)
   - Bugs categorized by severity (critical, major, minor)
   - Bugs prioritized for fixing
4. Bug fixes implemented:
   - All critical bugs fixed before MVP release
   - Major bugs fixed or documented as known issues
   - Minor bugs triaged for post-MVP
5. Regression testing:
   - After bug fixes, rerun integration tests
   - Verify fixes don't break existing functionality
6. User acceptance testing:
   - If possible, have another user test the system
   - Collect feedback on UI usability
   - Collect feedback on generated documents quality

### Technical Notes:
- Use GitHub Issues or Jira for bug tracking
- Document test results in TEST_RESULTS.md
- Consider using pytest-bdd for behavior-driven testing
- Real-world testing: Use real LinkedIn/SEEK/Indeed searches but don't submit applications

---

## Story 6.7: Production Deployment Preparation

**As a** developer
**I want to** prepare the system for production deployment
**So that** it runs reliably in a production environment

### Acceptance Criteria:
1. Environment configuration:
   - Production .env file created (without secrets committed)
   - Environment variables documented
   - Secrets management strategy (use AWS Secrets Manager or similar)
2. Deployment options documented:
   - **Local:** Run on personal computer with instructions
   - **Docker:** Dockerfile and docker-compose.yml for containerized deployment
   - **Cloud:** Deployment guide for AWS/GCP/Azure (EC2, Cloud Run, etc.)
3. Database backup strategy:
   - Automated daily backups of DuckDB file
   - Backup retention: 30 days
   - Restore procedure documented
4. Monitoring and alerting:
   - Health check endpoint (/health)
   - Prometheus metrics (optional)
   - Error alerting (email or Slack)
5. Security hardening:
   - API keys stored securely (not in code)
   - File permissions set correctly
   - No sensitive data in logs
   - HTTPS for Gradio UI (if accessible externally)
6. Resource requirements documented:
   - CPU: 2-4 cores recommended
   - RAM: 4-8 GB recommended
   - Disk: 10 GB minimum (for database and documents)
   - Network: Stable internet connection required
7. Maintenance procedures:
   - How to update configuration
   - How to restart workers
   - How to clear queue
   - How to reset database (if needed)

### Technical Notes:
- Use Docker for consistent deployment across environments
- Consider using docker-compose for multi-container setup (app, Redis, workers)
- Deployment guide should include step-by-step instructions with commands
- Provide systemd service file for Linux deployment

---

## Epic 6 Definition of Done

- [ ] All integration tests passing
- [ ] Error handling robust (retry logic, circuit breaker)
- [ ] Checkpoint resume tested and working
- [ ] Performance targets met (10 jobs/min per worker)
- [ ] Documentation complete and reviewed
- [ ] Real-world testing completed (7 days dry-run)
- [ ] All critical bugs fixed
- [ ] Production deployment guide ready
- [ ] System ready for MVP release! 🎉

---

## MVP Completion Checklist

### Functional Requirements
- [ ] Jobs discovered from LinkedIn, SEEK, and Indeed
- [ ] Duplicate detection working (Tier 1 and Tier 2)
- [ ] 7-agent pipeline processing jobs correctly
- [ ] CV and CL tailored per job
- [ ] Applications submitted via email and web forms
- [ ] Checkpoint/resume system operational

### User Interface
- [ ] Dashboard showing metrics and status
- [ ] Pipeline view showing real-time agent flow
- [ ] Pending jobs management page
- [ ] Approval mode functional
- [ ] Dry-run mode functional
- [ ] Application history searchable

### Quality
- [ ] Integration tests passing
- [ ] Error handling robust
- [ ] Performance acceptable (10+ jobs/min)
- [ ] Real-world testing completed
- [ ] Critical bugs fixed

### Documentation
- [ ] Setup guide complete
- [ ] User guide complete
- [ ] Architecture documented
- [ ] Troubleshooting guide available

### Deployment
- [ ] Docker configuration ready
- [ ] Production deployment tested
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting configured

**Once all items checked: MVP RELEASE! 🚀**
