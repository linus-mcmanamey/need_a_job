# 7. Agent Architecture

## 7.1 Agent Taxonomy

```
BaseAgent (Abstract)
│
├── JobMatcherAgent
│   ├── Reads: Job description, search.yaml
│   ├── Uses: Claude (Sonnet) to score match
│   └── Outputs: match_score, matched_criteria
│
├── SalaryValidatorAgent
│   ├── Reads: Job salary field
│   ├── Uses: Simple logic (threshold check)
│   └── Outputs: salary_aud_per_day, meets_threshold
│
├── CVTailorAgent
│   ├── Reads: CV template, job requirements, match data
│   ├── Uses: Claude (Sonnet) to rewrite sections
│   └── Outputs: cv_file_path
│
├── CoverLetterWriterAgent
│   ├── Reads: CL template, job details, company info
│   ├── Uses: Claude (Sonnet) to customize letter
│   └── Outputs: cl_file_path, contact_person_name
│
├── QAAgent
│   ├── Reads: Generated CV/CL files
│   ├── Uses: Claude (Sonnet) to validate quality
│   └── Outputs: qa_status (pass/fail), issues[]
│
├── OrchestratorAgent
│   ├── Reads: All previous agent outputs
│   ├── Uses: Claude (Opus) for final decision
│   └── Outputs: final_decision (approve/reject), reasoning
│
└── ApplicationFormHandlerAgent
    ├── Reads: Job application_url/email
    ├── Uses: Email API or Playwright/Chrome MCP
    └── Outputs: submission_status, submitted_timestamp
```

## 7.2 Agent Communication Pattern

**Sequential Pipeline with Shared Context:**

```python
class JobContext:
    """Shared context passed through agent pipeline"""
    job_id: str
    job_data: Job
    agent_outputs: Dict[str, AgentResult]  # Accumulates outputs

    def add_output(self, agent_name: str, result: AgentResult):
        self.agent_outputs[agent_name] = result

    def get_output(self, agent_name: str) -> AgentResult:
        return self.agent_outputs.get(agent_name)

# In AgentOrchestrator
context = JobContext(job_id=job_id, job_data=job)

for agent in self.agents:
    result = agent.execute(context)  # Agent can read previous outputs
    context.add_output(agent.name, result)

    if result.decision == Decision.REJECT:
        break
```

## 7.3 Agent Model Selection Strategy

| Agent | Claude Model | Reasoning |
|-------|-------------|-----------|
| JobMatcherAgent | claude-sonnet-4 | Requires reasoning about criteria matching |
| SalaryValidatorAgent | claude-haiku | Simple threshold check, use cheapest model |
| CVTailorAgent | claude-sonnet-4 | Critical document quality, needs strong model |
| CoverLetterWriterAgent | claude-sonnet-4 | Critical document quality, needs strong model |
| QAAgent | claude-sonnet-4 | Quality validation requires strong reasoning |
| OrchestratorAgent | claude-opus | Final decision, use most powerful model |
| ApplicationFormHandlerAgent | claude-sonnet-4 | Form automation, moderate complexity |

**Cost Optimization (V2):**
- Cache system prompts (reuse across jobs)
- Batch similar jobs (if API supports batching)
- Use prompt caching for search criteria (from search.yaml)

---
