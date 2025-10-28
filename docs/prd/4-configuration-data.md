# 4. Configuration & Data

## 4.1 Search Criteria Configuration

Based on `create2.md`, extracted to `search.yaml`:

```yaml
job_type: contract
duration: 3-12+ months

locations:
  primary: Remote (Australia-wide)
  secondary: Hobart, Tasmania
  acceptable: Hybrid with >70% remote

keywords:
  primary:
    - "data engineer"
    - "data engineering"

  secondary:
    - "Azure Data Engineer"
    - "AWS Data Engineer"
    - "PySpark Developer"
    - "Data Platform Engineer"
    - "Synapse Analytics"
    - "Databricks Engineer"
    - "ETL Developer"
    - "Data Pipeline Engineer"
    - "Analytics Engineer"

technologies:
  must_have:
    - Python
    - SQL
    - Cloud Platform (Azure/AWS/GCP)

  strong_preference:
    - PySpark
    - Azure Synapse
    - Data Factory
    - Databricks
    - Airflow
    - dbt
    - MCP
    - LLM/AI

  nice_to_have:
    - Docker
    - Kubernetes
    - Terraform
    - CI/CD
    - Git

salary_expectations:
  minimum: 800  # AUD per day
  target: 1000
  maximum: 1500
```

## 4.2 Agent Configuration

`agents.yaml`:

```yaml
job_matcher_agent:
  model: claude-sonnet-4  # Or specific Claude model
  match_threshold: 0.70  # Minimum score to proceed
  scoring_weights:
    must_have_present: 0.50
    strong_preference_present: 0.30
    nice_to_have_present: 0.10
    location_match: 0.10

salary_validator_agent:
  model: claude-haiku  # Lightweight for simple validation
  min_salary: 800
  max_salary: 1500
  missing_salary_action: flag_for_review

cv_tailor_agent:
  model: claude-sonnet-4
  template_path: current_cv_coverletter/Linus_McManamey_CV.docx
  output_directory: export_cv_cover_letter/{date}_{company}_{title}/
  customization_level: moderate  # conservative|moderate|aggressive

cover_letter_writer_agent:
  model: claude-sonnet-4
  template_path: current_cv_coverletter/Linus_McManamey_CL.docx
  output_directory: export_cv_cover_letter/{date}_{company}_{title}/
  tone: professional_friendly

qa_agent:
  model: claude-sonnet-4
  checks:
    - australian_english
    - formatting_consistency
    - no_fabrication
    - contact_info_accuracy
  strict_mode: true  # Fail on any issue

orchestrator_agent:
  model: claude-opus  # Most powerful for final decisions
  approval_policy: require_3_way  # Job Matcher + QA + Orchestrator

application_form_handler_agent:
  model: claude-sonnet-4
  timeout_seconds: 120
  captcha_handling: mark_pending
  complex_form_handling: mark_pending
```

## 4.3 Platform Configuration

`platforms.yaml`:

```yaml
linkedin:
  type: mcp_server
  server_name: linkedin
  enabled: true
  polling_interval: 3600  # seconds (1 hour)
  rate_limit: 100  # requests per hour

seek:
  type: web_scraping
  enabled: true
  base_url: https://www.seek.com.au
  search_url: /data-engineer-jobs
  polling_interval: 3600
  rate_limit: 50

indeed:
  type: web_scraping
  enabled: true
  base_url: https://au.indeed.com
  search_url: /jobs?q=data+engineer
  polling_interval: 3600
  rate_limit: 50

# V2: Easy to add new platforms
# jora:
#   type: yaml_config
#   config_file: platforms/jora.yaml
```

## 4.4 Similarity Algorithm Configuration

```yaml
duplicate_detection:
  tier_1:  # Fast fuzzy matching
    algorithms:
      title: token_set_ratio
      company: fuzzy_match
      description: fuzzy_match
      location: fuzzy_normalized

    weights:
      title: 0.20
      company: 0.10
      description: 0.50
      location: 0.20

    thresholds:
      auto_group: 0.90
      deep_analysis_min: 0.75
      different_jobs: 0.75

  tier_2:  # LLM embedding similarity (for 75-89% scores)
    algorithms:
      title: embeddings
      company: embeddings
      description: embeddings
      location: geo_coding

    weights:  # Same as tier_1
      title: 0.20
      company: 0.10
      description: 0.50
      location: 0.20

    embedding_model: claude  # or openai, local
    threshold: 0.90
```

---
