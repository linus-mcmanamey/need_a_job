# Data Engineering Contract Roles - Job Search System

## Configuration

### Search Parameters
```yaml
job_type: contract
locations:
  - remote:
      scope: Australia
      preference: primary
  - physical:
      city: Hobart
      state: Tasmania
      country: Australia
      preference: secondary
keywords:
  primary:
    - "data engineering"
    - "data engineer"
  secondary:
    - "Azure Data Engineer"
    - "PySpark Developer"
    - "Data Platform Engineer"
    - "ETL Developer"
    - "Synapse Developer"
    - "AWS Data Engineer"
    - "Databricks Engineer"
search_date: 2025-10-18
auto_refresh: true
refresh_interval: daily
```

### MCP Server Integration
```yaml
mcp_servers:
  job_search:
    enabled: true
    servers:
      - linkedin_scraper
      - seek_api
      - indeed_api
      - web_search
    capabilities:
      - fetch_jobs
      - parse_descriptions
      - extract_requirements
      - match_skills
      - track_applications

  data_processing:
    enabled: true
    servers:
      - text_analysis
      - data_extraction
    capabilities:
      - extract_key_requirements
      - analyze_skill_match
      - generate_summaries
```

## Search Endpoints

### Primary Sources
```json
{
  "linkedin": {
    "base_url": "https://www.linkedin.com/jobs/search/",
    "queries": [
      {
        "name": "remote_data_engineering",
        "params": {
          "keywords": "data engineering contract",
          "location": "Australia",
          "f_WT": "2",
          "f_JT": "C"
        }
      },
      {
        "name": "hobart_data_engineering",
        "params": {
          "keywords": "data engineering",
          "location": "Hobart, Tasmania, Australia",
          "f_JT": "C"
        }
      },
      {
        "name": "tasmania_broad",
        "params": {
          "keywords": "data engineering",
          "location": "Tasmania, Australia",
          "f_JT": "C",
          "f_WT": "1,2"
        }
      }
    ]
  },
  "seek": {
    "base_url": "https://www.seek.com.au/",
    "queries": [
      {
        "endpoint": "data-engineering-jobs/in-All-Tasmania",
        "filters": ["contract"]
      }
    ]
  },
  "indeed": {
    "base_url": "https://au.indeed.com/jobs",
    "queries": [
      {
        "params": {
          "q": "data engineering contract",
          "l": "Tasmania"
        }
      }
    ]
  }
}
```

## Job Data Schema

### Job Entry Template
```yaml
job:
  id: <auto_generated>
  source: <platform_name>
  fetch_date: <timestamp>

  details:
    title: string
    company: string
    location:
      type: [remote|onsite|hybrid]
      city: string
      state: string
      country: string
    posted_date: date
    contract_duration: string
    salary_range: string

  description:
    raw: string
    parsed:
      summary: string
      responsibilities: array
      requirements: array
      nice_to_have: array

  matching:
    skill_match_score: float
    requirement_match: object
    keywords_found: array

  metadata:
    url: string
    application_deadline: date
    recruiter: string
    contact_info: string

  status:
    viewed: boolean
    applied: boolean
    application_date: date
    response: string
    notes: string
```

## Automated Job Collection

### MCP Task Definitions

```javascript
// MCP task configuration for automated job collection
const jobSearchTasks = {
  "daily_search": {
    "frequency": "daily",
    "time": "09:00",
    "actions": [
      "fetch_new_jobs",
      "parse_descriptions",
      "calculate_match_scores",
      "update_database",
      "generate_report"
    ]
  },

  "on_demand_search": {
    "trigger": "manual",
    "actions": [
      "search_all_platforms",
      "deduplicate_results",
      "rank_by_relevance",
      "export_results"
    ]
  },

  "application_tracking": {
    "trigger": "on_update",
    "actions": [
      "update_status",
      "log_activity",
      "set_reminders"
    ]
  }
}
```

## Current Jobs Database

### Active Opportunities
<!-- Last Updated: 2025-10-18 -->
```yaml
jobs:
  - id: DE001
    source: LinkedIn
    fetch_date: 2025-10-18
    details:
      title: Senior Data Engineer - Remote
      company: Major Australian Not-For-Profit
      location:
        type: remote
        scope: Australia
      contract_duration: 6-12 months
      salary_range: $800-$1,150/day inc super
    description:
      summary: Immediate start opportunity for experienced Data Engineer
      key_requirements:
        - Azure Data Factory
        - Python
        - SQL
        - Data pipeline development
    metadata:
      url: https://www.linkedin.com/jobs/search/?keywords=data%20engineering%20contract&location=Australia&f_WT=2&f_JT=C
      status: Active

  - id: DE002
    source: SEEK
    fetch_date: 2025-10-18
    details:
      title: Principal Data Engineer
      company: Australian Tech Giant
      location:
        type: hybrid
        city: Sydney/Melbourne
        remote_percentage: 90%
      contract_duration: 12+ months
      salary_range: $1,100-$1,250/day + GST
    description:
      summary: Short term contract for Principal Data Engineer
      key_requirements:
        - Python
        - SQL
        - Excel
        - Front office finance/trading experience
    metadata:
      url: https://www.seek.com.au/data-engineer-jobs/contract-temp
      status: Active

  - id: DE003
    source: SEEK
    fetch_date: 2025-10-18
    details:
      title: Azure Data Engineer
      company: Various (528 positions available)
      location:
        type: remote/hybrid
        scope: Australia-wide
      contract_duration: 3-6 months typical
      salary_range: Market rates
    description:
      summary: Multiple Azure Data Engineer contract positions available
      key_requirements:
        - Azure Data Factory
        - Azure Fabric
        - Python
        - SQL
        - Data pipelines
    metadata:
      url: https://www.seek.com.au/azure-data-engineer-jobs
      status: Active

  - id: DE004
    source: LinkedIn
    fetch_date: 2025-10-18
    details:
      title: Data Engineer - Federal Government
      company: Federal Government Department
      location:
        type: hybrid
        city: Hobart
        scope: Multiple locations including Hobart
      contract_duration: Long-term contract
      salary_range: Lucrative hourly rates
    description:
      summary: On-demand IT Support resources for Federal Government
      key_requirements:
        - Data engineering experience
        - Government experience preferred
        - Australian citizenship required
    metadata:
      url: https://au.linkedin.com/jobs/search
      status: Active

  - id: DE005
    source: SEEK
    fetch_date: 2025-10-18
    details:
      title: Software/Senior Software Engineer - Data Focus
      company: AODN (Australian Ocean Data Network)
      location:
        type: hybrid
        city: Hobart
        state: Tasmania
      contract_duration: Permanent (contract conversion possible)
      salary_range: Competitive
    description:
      summary: Deliver and manage high-volume environmental data
      key_requirements:
        - Data pipeline development
        - High-volume data processing
        - Cloud platforms
        - Python/SQL
    metadata:
      url: https://www.seek.com.au/Data-Engineering-jobs/in-All-Hobart-TAS
      status: Active
```

### Application Tracking

| ID | Company | Role | Platform | Applied | Status | Match Score | Notes |
|----|---------|------|----------|---------|--------|-------------|-------|
| DE001 | Major Not-For-Profit | Senior Data Engineer | LinkedIn | ❌ | Not Applied | High | Remote, good rate |
| DE002 | Tech Giant | Principal Data Engineer | SEEK | ❌ | Not Applied | Medium | High rate, needs finance exp |
| DE003 | Various | Azure Data Engineer | SEEK | ❌ | Not Applied | High | Multiple opportunities |
| DE004 | Federal Gov | Data Engineer | LinkedIn | ❌ | Not Applied | Medium | Requires citizenship |
| DE005 | AODN | Software Engineer - Data | SEEK | ❌ | Not Applied | High | Hobart-based, interesting domain |

## Analytics & Insights

### Search Performance
```yaml
metrics:
  total_jobs_found: 5
  total_applications: 0
  response_rate: 0
  average_match_score: 0.8

  by_platform:
    linkedin: { found: 218, applied: 0, responses: 0 }
    seek: { found: 528, applied: 0, responses: 0 }
    indeed: { found: 0, applied: 0, responses: 0 }

  by_location:
    remote: { found: 3, applied: 0 }
    hobart: { found: 2, applied: 0 }
    tasmania_other: { found: 0, applied: 0 }
```

### Skill Gap Analysis
<!-- Based on current job market analysis -->
```yaml
frequently_required_skills:
  high_demand:
    - Azure Data Factory (4/5 jobs)
    - Python (5/5 jobs)
    - SQL (5/5 jobs)
    - Data Pipeline Development (5/5 jobs)
    - Azure Fabric (trending)

  moderate_demand:
    - Databricks
    - Apache Spark
    - AWS
    - Snowflake
    - DBT (Data Build Tool)

  specialized:
    - Front office finance/trading (for high-rate contracts)
    - Government experience (for federal contracts)
    - Environmental data (for specific domains)

market_insights:
  - Contract rates: $800-$1,250/day
  - Most contracts: 3-12 months duration
  - Remote work: 90%+ positions offer remote/hybrid
  - Hobart opportunities: Limited but available (Federal Gov, AODN)
```

## MCP Server Commands

### Available Commands
```bash
# Fetch new jobs from all configured sources
mcp run job_search.fetch_all

# Search specific platform
mcp run job_search.fetch --platform=linkedin

# Analyze job description
mcp run job_analysis.analyze --url="<job_url>"

# Update application status
mcp run tracking.update --job_id="<id>" --status="<status>"

# Generate weekly report
mcp run reporting.weekly_summary

# Export to CSV
mcp run export.csv --file="jobs_export.csv"
```

## Configuration Files

### .mcp.json Integration
```json
{
  "job_search": {
    "config_path": "./job_search_config.yaml",
    "data_path": "./job_data/",
    "export_path": "./exports/",
    "log_level": "info"
  }
}
```

## Notes & Preferences

### Search Strategy
- Prioritize remote positions within Australia
- Check if "Remote within Australia" vs "Remote anywhere"
- Apply to positions that offer remote from Tasmania even if not explicit
- Focus on 6-12 month contracts with potential for extension

### Keywords Priority
1. High priority: data engineering, ETL, pipeline, Azure, AWS
2. Medium priority: Python, SQL, Spark, Databricks
3. Low priority: visualization, reporting, analytics

### Auto-rejection Criteria
- Requires security clearance (unless already held)
- On-site only with no flexibility
- Less than 3-month contracts
- Junior/Graduate positions

---

*Last Updated: 2025-10-18*
*MCP Integration Version: 1.0*