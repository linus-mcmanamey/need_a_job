# Epic 3: Duplicate Detection (Weeks 3-4)

**Epic Goal:** Implement multi-platform job discovery with intelligent duplicate detection to prevent multiple applications to the same job.

**Epic Value:** Expands job discovery to all major platforms and prevents embarrassing duplicate applications.

**Timeline:** Weeks 3-4

**Deliverable:** Multi-platform job discovery with deduplication working

---

## Story 3.1: SEEK Job Poller

**As a** system
**I want to** search SEEK for jobs matching my criteria
**So that** I discover jobs from Australia's largest job platform

### Acceptance Criteria:
1. SEEK web scraper implemented (REQ-001):
   - Base URL: https://www.seek.com.au
   - Search: /data-engineer-jobs with location filters
   - Rate limiting: 50 requests/hour
2. Job metadata extraction (REQ-003):
   - Company name, job title, salary, location, posting date
   - Full job description, requirements, responsibilities
   - Platform source (seek) and job URL
3. Poller runs on same interval as LinkedIn (1 hour)
4. New jobs inserted into `jobs` table with platform_source='seek'
5. Handles SEEK-specific formats:
   - Salary ranges ("$100k-$120k")
   - Location variations ("Melbourne CBD", "Remote - VIC")
6. Handles scraping challenges:
   - JavaScript-rendered content (use Playwright if needed)
   - Anti-bot measures (user agent, delays between requests)
   - Pagination (multi-page results)
7. Error handling:
   - Invalid HTML structure (log and skip job)
   - Network timeouts (retry with backoff)
   - Rate limit exceeded (wait and resume)

### Technical Notes:
- Use BeautifulSoup or Playwright for scraping
- Respect robots.txt
- Add random delays (2-5 seconds) between requests
- Store raw HTML for debugging (optional)
- Consider using proxies if rate limited frequently

---

## Story 3.2: Indeed Job Poller

**As a** system
**I want to** search Indeed for jobs matching my criteria
**So that** I discover jobs from the global job platform

### Acceptance Criteria:
1. Indeed web scraper implemented (REQ-001):
   - Base URL: https://au.indeed.com
   - Search: /jobs?q=data+engineer with location filters
   - Rate limiting: 50 requests/hour
2. Job metadata extraction (REQ-003):
   - Company name, job title, salary, location, posting date
   - Full job description (requires clicking through to job page)
   - Platform source (indeed) and job URL
3. Poller runs on same interval as other platforms (1 hour)
4. New jobs inserted into `jobs` table with platform_source='indeed'
5. Handles Indeed-specific formats:
   - Salary estimates vs actual salary
   - "Easily apply" jobs vs external applications
   - Sponsored vs organic results
6. Two-step scraping:
   - Step 1: Search results page (job listings)
   - Step 2: Individual job pages (full descriptions)
7. Error handling similar to SEEK poller

### Technical Notes:
- Indeed has stricter anti-bot measures than SEEK
- May require Playwright for JavaScript rendering
- Consider caching job detail pages (1 hour) to avoid refetching
- Job IDs from URL: extract and use for deduplication

---

## Story 3.3: Tier 1 Duplicate Detection (Fuzzy Matching)

**As a** system
**I want to** quickly identify obvious job duplicates using fuzzy matching
**So that** I don't waste time on detailed analysis for every job pair

### Acceptance Criteria:
1. Fuzzy matching algorithms implemented (REQ-002, Section 4.4):
   - Title: token_set_ratio (RapidFuzz)
   - Company: fuzzy_match (basic string similarity)
   - Description: fuzzy_match (first 500 characters)
   - Location: fuzzy_normalized (handle variations)
2. Weighted scoring applied:
   - Title: 20%
   - Company: 10%
   - Description: 50%
   - Location: 20%
3. Similarity score calculated for each new job against recent jobs:
   - Compare against jobs from last 30 days
   - Calculate combined similarity score (0.0 to 1.0)
4. Thresholds applied (REQ-002):
   - ≥ 90%: Auto-group as duplicate
   - 75-89%: Flag for Tier 2 deep analysis
   - < 75%: Different jobs
5. Duplicate grouping:
   - Create duplicate_group_id for first job in group
   - Assign same duplicate_group_id to duplicates
6. Database updates:
   - Set duplicate_group_id in jobs table
   - Create application_tracking with status="duplicate" for secondary jobs
   - Primary job (first discovered) remains active
7. Logs duplicate detection decisions

### Technical Notes:
- Use RapidFuzz library for fast fuzzy matching
- Normalize strings: lowercase, remove punctuation, trim whitespace
- Location normalization: "Hobart, TAS" == "Hobart, Tasmania" == "Hobart"
- Consider using background task for comparison (can be slow with many jobs)
- Optimize: Only compare against jobs with similar titles (pre-filter)

---

## Story 3.4: Tier 2 Duplicate Detection (LLM Embeddings)

**As a** system
**I want to** use LLM embeddings for deep similarity analysis on borderline matches
**So that** I accurately detect duplicates that fuzzy matching misses

### Acceptance Criteria:
1. Embedding generation implemented (REQ-002, Section 4.4):
   - Model: Claude embeddings API (or OpenAI as fallback)
   - Generate embeddings for:
     - Job title
     - Company name
     - Full job description
     - Location (geocoded coordinates)
2. Embedding similarity calculated:
   - Cosine similarity between embedding vectors
   - Weighted scoring (same as Tier 1):
     - Title: 20%
     - Company: 10%
     - Description: 50%
     - Location: 20%
3. Triggered only for 75-89% Tier 1 matches:
   - Batch processing (multiple jobs at once)
   - Skip if Tier 1 score < 75% or ≥ 90%
4. Final decision threshold: 90% (REQ-002):
   - ≥ 90%: Group as duplicate
   - < 90%: Mark as different jobs
5. Caching implemented:
   - Store embeddings in database (new column in jobs table)
   - Reuse embeddings for future comparisons
   - Refresh embeddings if job description changes
6. Performance optimization:
   - Async embedding generation
   - Rate limiting for API calls
   - Batch requests (up to 10 jobs per API call)
7. Logs Tier 2 analysis and decisions

### Technical Notes:
- Use Anthropic Claude or OpenAI embedding models
- Store embeddings as binary vectors (pickle or msgpack)
- Consider using vector database (e.g., FAISS) for large-scale similarity search
- Embedding dimensions: 1536 (OpenAI) or 1024 (Claude)
- Location geocoding: Use geopy or Google Maps API

---

## Story 3.5: Duplicate Application Strategy

**As a** system
**I want to** apply to ALL platform instances of a job if it meets criteria
**So that** I maximize visibility across platforms

### Acceptance Criteria:
1. Duplicate group processing implemented (REQ-011):
   - Apply to all jobs in duplicate group (not just primary)
   - Each application customized for platform specifics:
     - Company name variations ("Company Pty Ltd" vs "Company")
     - Platform-specific fields (SEEK vs LinkedIn vs Indeed)
     - Job URL (different per platform)
2. Salary data sharing within group (REQ-011):
   - If one job in group has salary, apply to all jobs in group
   - Copy salary to missing_salary jobs
   - Note salary source (which platform provided it)
3. Document reuse within group:
   - Generate CV/CL once for primary job
   - Reuse same documents for duplicate jobs
   - Update only platform-specific references
4. Application tracking per platform:
   - Separate application_tracking record for each platform instance
   - All reference same duplicate_group_id
   - Track submission status independently per platform
5. Prevent redundant processing:
   - Agent pipeline runs once for group (on primary job)
   - Other jobs in group skip to "ready_to_send" status
   - Copy stage_outputs from primary job
6. UI shows grouped jobs:
   - Display as single entry with multiple platform badges
   - Show which platforms have been applied to

### Technical Notes:
- Primary job: First discovered job in group (earliest discovered_timestamp)
- Platform variations: Store in JSON field (platform_specific_data)
- Consider user preference: "Apply to all platforms" vs "Apply to best platform only"
- Future enhancement: Track response rates per platform

---

## Epic 3 Definition of Done

- [ ] SEEK and Indeed pollers operational
- [ ] Jobs discovered from all 3 platforms (LinkedIn, SEEK, Indeed)
- [ ] Tier 1 fuzzy matching detects obvious duplicates (≥90%)
- [ ] Tier 2 LLM embeddings analyzes borderline matches (75-89%)
- [ ] Duplicate jobs grouped with same duplicate_group_id
- [ ] Application strategy applies to all platform instances
- [ ] Salary data shared within duplicate groups
- [ ] End-to-end test: Same job from multiple platforms → grouped → applied to all
- [ ] Documentation: Duplicate detection algorithm and configuration
