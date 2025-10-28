# Epic 5: Gradio UI (Weeks 5-6)

**Epic Goal:** Build a Gradio web interface for monitoring the job pipeline, managing pending jobs, and controlling system behavior.

**Epic Value:** Provides visibility and control over the automated system, enabling user intervention when needed.

**Timeline:** Weeks 5-6

**Deliverable:** Functional UI for monitoring and control

---

## Story 5.1: Dashboard Page - Overview Metrics

**As a** user
**I want to** see real-time metrics about job discovery and applications
**So that** I can monitor system activity at a glance

### Acceptance Criteria:
1. Dashboard displays key metrics (REQ-013):
   - **Jobs discovered today:** Count of jobs added to database today
   - **Applications sent:** Count of completed applications (all time and today)
   - **Pending count:** Jobs requiring manual intervention
   - **Success rate:** % of discovered jobs that led to completed applications
2. Metrics refresh automatically:
   - Polling interval: 30 seconds
   - Or use WebSocket for real-time updates
3. Status breakdown widget (REQ-013):
   - Count by status: discovered, matched, documents_generated, ready_to_send, sending, completed, pending, failed, rejected, duplicate
   - Visual representation: Bar chart or donut chart
   - Color coding: Green (completed), Yellow (in-progress), Red (failed/rejected), Gray (pending)
4. Recent activity feed (REQ-013):
   - Last 10 jobs processed
   - Show: Job title, company, status, timestamp
   - Clickable to view job details
5. System health indicators:
   - Worker status: Number of active RQ workers
   - Queue depth: Number of jobs waiting in queue
   - Error count: Number of failed jobs in last hour
6. Time range selector:
   - Filter metrics by: Today, Last 7 days, Last 30 days, All time

### Technical Notes:
- Use Gradio components: gr.Number, gr.BarPlot, gr.DataFrame
- Query DuckDB for aggregated metrics
- Cache queries for 30 seconds to reduce database load
- Use Gradio's auto-refresh with gr.update()

---

## Story 5.2: Job Pipeline Page - Real-time Agent Flow

**As a** user
**I want to** watch jobs flow through the agent pipeline in real-time
**So that** I can see the system working and identify bottlenecks

### Acceptance Criteria:
1. Pipeline visualization displays (REQ-014):
   - Jobs currently in each agent stage
   - Job title, company, current stage
   - Time in current stage (seconds/minutes)
   - Color-coded status:
     - Green: Success
     - Yellow: In progress
     - Red: Failed
     - Blue: Waiting
2. Real-time updates (REQ-014):
   - WebSocket connection to backend
   - Updates push to UI when job moves to new stage
   - No page refresh required
3. Agent execution metrics (REQ-014):
   - Average execution time per agent
   - Agent success rate (% of jobs passing)
   - Current agent throughput (jobs/minute)
4. Job detail modal:
   - Click job to see full details
   - Show: Job description, agent outputs, status history
   - Link to CV/CL files (download)
5. Pipeline stage view:
   - Visual pipeline: Discovery → Matcher → Salary → CV → CL → QA → Orchestrator → Submission
   - Show count of jobs at each stage
   - Identify bottlenecks (stages with high job count)
6. Filters:
   - Filter by platform (LinkedIn, SEEK, Indeed)
   - Filter by status (in-progress, completed, failed)
   - Search by job title or company

### Technical Notes:
- Use WebSocket (websockets library) for real-time updates
- Gradio Live components for automatic updates
- Consider using Plotly for interactive pipeline visualization
- Polling fallback if WebSocket not available

---

## Story 5.3: Pending Jobs Management Page

**As a** user
**I want to** view and manage jobs that require manual intervention
**So that** I can complete pending applications and retry failed ones

### Acceptance Criteria:
1. Pending jobs list displays (REQ-015):
   - All jobs with status="pending" or status="failed"
   - Show: Job title, company, platform, error details, timestamp
   - Sortable by timestamp (newest first)
2. Error details shown (REQ-015):
   - Which agent failed
   - Error message
   - Last successful stage
   - Agent outputs from completed stages
3. Action buttons per job (REQ-015):
   - **Retry:** Resume from failed agent
     - Clears error_info
     - Updates status to resume pipeline
     - Enqueues job for processing
   - **Skip:** Mark as rejected
     - Updates status to "rejected"
     - Records skip reason
   - **Manual Complete:** Mark as completed outside system
     - Updates status to "completed"
     - Records manual completion timestamp
   - **View Details:** Open job detail modal
4. Bulk actions:
   - Select multiple jobs (checkboxes)
   - Bulk retry
   - Bulk skip
5. Filters and search:
   - Filter by error type (complex_form, api_error, validation_error)
   - Filter by platform
   - Search by job title or company
6. Manual intervention guidance:
   - For complex forms: Link to application URL
   - For missing data: Show what data is needed
   - For API errors: Show retry recommendations

### Technical Notes:
- Use Gradio DataFrame for job list
- Action buttons: gr.Button with onclick callbacks
- Bulk actions: Use gr.CheckboxGroup
- Pagination: Show 20 jobs per page

---

## Story 5.4: Approval Mode

**As a** user
**I want to** review and approve applications before they're sent
**So that** I maintain control over what gets submitted on my behalf

### Acceptance Criteria:
1. Approval mode toggle (REQ-016):
   - UI toggle: "Require approval before sending applications"
   - When enabled: Jobs stop at "ready_to_send" status
   - When disabled: Jobs proceed automatically to Application Form Handler
   - Toggle state persists (stored in config or database)
2. Pending approvals view (REQ-016):
   - List all jobs with status="ready_to_send"
   - Show: Job title, company, match score, salary
   - Preview CV and CL (embedded or download)
3. Approval actions per job (REQ-016):
   - **Approve:** Proceed with application
     - Enqueues job for Application Form Handler
     - Updates status to "sending"
   - **Reject:** Don't apply to this job
     - Updates status to "rejected"
     - Records rejection reason
   - **Edit:** Modify CV/CL before approving (future enhancement)
4. Bulk approval (REQ-016):
   - Select multiple jobs
   - Approve all selected
   - Reject all selected
5. Approval summary:
   - Count of pending approvals
   - Average match score of pending jobs
   - Oldest pending job (time waiting for approval)
6. Auto-reminder:
   - If > 10 pending approvals, show notification
   - If pending approval > 24 hours old, highlight

### Technical Notes:
- Store approval_required setting in database or config file
- Use gr.Checkbox for toggle
- CV/CL preview: Use gr.File or embed PDF viewer
- Implement approval queue (FIFO or priority-based)

---

## Story 5.5: Dry-Run Mode

**As a** user
**I want to** test the system without sending real applications
**So that** I can validate CV/CL generation and agent decisions safely

### Acceptance Criteria:
1. Dry-run mode toggle (REQ-017):
   - UI toggle: "Dry-run mode (generate but don't send)"
   - When enabled: Pipeline stops before Application Form Handler
   - When disabled: Pipeline runs end-to-end
   - Toggle state persists
2. Dry-run behavior (REQ-017):
   - Jobs flow through all agents up to Orchestrator
   - CV and CL files generated and saved
   - Application Form Handler skipped
   - Jobs marked with status="dry_run_complete"
3. Dry-run results view:
   - List all dry-run jobs
   - Show: Job title, company, match score, orchestrator decision
   - Download generated CV/CL files
   - View all agent outputs (full pipeline results)
4. Dry-run testing scenarios:
   - Test configuration changes (new keywords, thresholds)
   - Test document generation (CV/CL customization)
   - Test agent decisions (which jobs get approved)
5. Dry-run to live conversion:
   - "Send Now" button for dry-run jobs
   - Moves job from "dry_run_complete" to "ready_to_send"
   - Proceeds with actual application submission
6. Dry-run analytics:
   - Count of jobs that would have been applied to
   - Average match score
   - Most common rejection reasons

### Technical Notes:
- Store dry_run_enabled setting in database or config file
- Add status value: "dry_run_complete"
- Consider separate dry-run database (future enhancement)
- Dry-run jobs can be deleted after review (don't clutter main DB)

---

## Story 5.6: Application History and Search

**As a** user
**I want to** search and view my application history
**So that** I can track which jobs I've applied to and when

### Acceptance Criteria:
1. Application history table:
   - All applications with status="completed"
   - Show: Job title, company, platform, submitted date, match score
   - Sortable by any column
   - Paginated (50 per page)
2. Search functionality:
   - Search by job title
   - Search by company name
   - Filter by platform (LinkedIn, SEEK, Indeed)
   - Filter by date range (last 7 days, last 30 days, custom)
   - Filter by match score range (0.7-0.8, 0.8-0.9, 0.9-1.0)
3. Application detail view:
   - Click application to see full details
   - Job description
   - Match criteria (which requirements were met)
   - Agent outputs (all stages)
   - Generated CV/CL (download links)
   - Submission confirmation (timestamp, method, details)
4. Export functionality:
   - Export search results to CSV
   - Include: job_id, title, company, platform, submitted_date, match_score, salary
5. Statistics:
   - Total applications submitted
   - Applications per platform
   - Average match score
   - Applications per week (trend chart)

### Technical Notes:
- Use Gradio DataFrame with search and filter
- Full-text search on title and company (DuckDB FTS)
- Date range picker: gr.DatePicker
- CSV export: Use pandas to_csv()

---

## Epic 5 Definition of Done

- [ ] Dashboard page shows real-time metrics and status breakdown
- [ ] Pipeline page displays live agent flow with WebSocket updates
- [ ] Pending jobs page lists errors and provides retry/skip actions
- [ ] Approval mode functional (review and approve before sending)
- [ ] Dry-run mode functional (test without sending applications)
- [ ] Application history searchable and exportable
- [ ] UI accessible from browser (http://localhost:7860 or custom port)
- [ ] UI styling consistent and user-friendly
- [ ] Documentation: UI user guide with screenshots
