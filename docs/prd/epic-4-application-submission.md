# Epic 4: Application Submission (Weeks 4-5)

**Epic Goal:** Implement the Application Form Handler agent to automatically submit applications via email and web forms.

**Epic Value:** Completes the end-to-end automation from job discovery to application submission.

**Timeline:** Weeks 4-5

**Deliverable:** End-to-end automation functional - jobs submitted automatically

---

## Story 4.1: Application Form Handler Agent Base

**As an** Application Form Handler Agent
**I want to** detect the submission method for each job
**So that** I can route to the appropriate submission handler

### Acceptance Criteria:
1. Agent reads job data and metadata (REQ-004)
2. Detects submission method (REQ-010):
   - **Email:** Job contains email address for applications
   - **Web form:** Job has "Apply" button or application URL
   - **External redirect:** Job redirects to company ATS (Workday, Greenhouse, etc.)
3. Stores submission method in application_tracking table
4. Routes to appropriate handler:
   - Email submission → Story 4.2
   - Simple web form → Story 4.3
   - Complex web form → Story 4.4
5. Handles detection failures:
   - No clear application method → mark as "pending"
   - Multiple methods available → prioritize email over web form
6. Logs submission method detection and routing decision

### Technical Notes:
- Email detection: Regex patterns for email addresses in description
- Web form detection: Check for application URLs, "Apply" buttons
- External ATS detection: Check domain (workday.com, greenhouse.io, lever.co, etc.)
- Store application_url in application_tracking for reference

---

## Story 4.2: Email Application Submission

**As an** Application Form Handler Agent
**I want to** send job applications via email
**So that** I can submit to email-based job postings

### Acceptance Criteria:
1. Composes email for application (REQ-009):
   - To: Company contact email (extracted from job posting)
   - Subject: "Application for [Job Title] - [Your Name]" or as specified in posting
   - Body: Professional email message (brief intro + "please find attached")
   - Attachments: CV and cover letter DOCX files
2. Email configuration from environment/config:
   - SMTP server settings
   - Sender email account (your email)
   - Authentication (username/password or OAuth)
3. Sends email using SMTP:
   - Connects to mail server
   - Authenticates
   - Sends message with attachments
   - Confirms delivery (SMTP response codes)
4. Tracks submission:
   - Updates application_tracking:
     - Status: "sending" → "completed"
     - submission_method: "email"
     - submitted_timestamp: current UTC time
   - Stores email recipient and subject in stage_outputs
5. Handles email errors:
   - Invalid recipient address → mark as "pending"
   - SMTP authentication failure → mark as "failed"
   - Attachment too large → compress or mark as "pending"
   - Network timeout → retry once, then mark as "failed"
6. Logs all email sending activity

### Technical Notes:
- Use Python smtplib or third-party library (yagmail)
- Email account: Use dedicated Gmail account with App Password
- Consider using SendGrid or AWS SES for better deliverability
- Email size limit: 25 MB (Gmail) - ensure CV+CL < 20 MB
- Rate limiting: Max 10 emails per hour (configurable)

---

## Story 4.3: Simple Web Form Submission

**As an** Application Form Handler Agent
**I want to** automatically fill and submit simple web forms
**So that** I can apply to jobs on platforms like SEEK and Indeed

### Acceptance Criteria:
1. Uses Playwright to automate browser (REQ-010):
   - Launches headless Chrome/Firefox
   - Navigates to application URL
   - Waits for page to load
2. Detects form fields automatically:
   - Name fields (first name, last name, full name)
   - Email address
   - Phone number
   - Resume/CV upload field
   - Cover letter upload field
   - Optional fields (LinkedIn profile, portfolio URL)
3. Fills form fields with data:
   - Name: "Linus McManamey"
   - Email: From config
   - Phone: From config
   - Resume: Upload CV file
   - Cover letter: Upload CL file
4. Handles simple form interactions:
   - Checkboxes (consent, terms & conditions)
   - Radio buttons (employment type, availability)
   - Dropdowns (years of experience, location preferences)
5. Submits form:
   - Clicks "Submit" or "Apply" button
   - Waits for confirmation page or success message
   - Takes screenshot of confirmation (save to logs)
6. Tracks submission:
   - Updates application_tracking:
     - Status: "sending" → "completed"
     - submission_method: "web_form"
     - submitted_timestamp: current UTC time
   - Stores form URL and screenshot path in stage_outputs
7. Handles form errors:
   - Missing required fields → mark as "pending"
   - File upload fails → retry once, then mark as "pending"
   - Submit button not clickable → mark as "pending"
   - Timeout (> 120 seconds) → mark as "failed"
8. Logs all browser automation steps

### Technical Notes:
- Use Playwright (configured in .mcp.json as mcp__playwright-server)
- Headless mode: true (for speed), false (for debugging)
- Form field detection: Use label text, placeholder text, or input name attributes
- Screenshot: Save to export_cv_cover_letter/{job_id}/confirmation.png
- Consider using Chrome MCP as alternative to Playwright

---

## Story 4.4: Complex Form Detection and Handling

**As an** Application Form Handler Agent
**I want to** detect complex forms that require manual intervention
**So that** I don't fail or submit incomplete applications

### Acceptance Criteria:
1. Detects complex form scenarios (REQ-010):
   - **CAPTCHA present:** reCAPTCHA, hCaptcha, image challenges
   - **Multi-step forms:** > 3 pages, progress indicators
   - **Custom questions:** Open-text selection criteria (250-500 words each)
   - **Video introduction:** Required video upload or recording
   - **Assessment tests:** Coding challenges, personality tests
   - **Document requirements:** Need for additional documents (certificates, portfolio)
2. On complex form detection:
   - Does NOT attempt to submit
   - Marks job as "pending"
   - Captures form screenshot
   - Logs complexity reason
3. Provides context for manual completion:
   - Application URL
   - Screenshot of form
   - Detected form fields (for reference)
   - Time estimate for manual completion
4. Updates application_tracking:
   - Status: "ready_to_send" → "pending"
   - Sets error_info:
     - error_type: "complex_form"
     - error_message: Specific reason (e.g., "CAPTCHA detected")
     - Timestamp
   - Stores form analysis in stage_outputs
5. User can manually complete from pending jobs UI:
   - Open application URL
   - Complete form manually
   - Mark as "completed" in system

### Technical Notes:
- CAPTCHA detection: Check for common CAPTCHA div IDs and classes
- Multi-step detection: Count forms, check for "Next" buttons
- Custom questions: Check for large textareas (> 200 char limit)
- Timeout for detection phase: 30 seconds
- Consider ML-based form complexity classifier (future enhancement)

---

## Story 4.5: Submission Status Tracking

**As a** system
**I want to** accurately track submission status for each application
**So that** I know which jobs have been applied to and which require intervention

### Acceptance Criteria:
1. Status values implemented (REQ-012):
   - `sending`: Application Form Handler in progress
   - `completed`: Successfully submitted
   - `pending`: Requires manual intervention
   - `failed`: Error occurred during submission
2. Status transitions tracked:
   - "ready_to_send" → "sending" (handler starts)
   - "sending" → "completed" (success)
   - "sending" → "pending" (complex form detected)
   - "sending" → "failed" (error occurred)
3. Submission metadata stored:
   - submitted_timestamp (UTC)
   - submission_method (email|web_form)
   - confirmation_details (confirmation number, screenshot path, email message ID)
4. Retry logic for failed submissions:
   - Failed submissions can be retried from UI
   - Max 3 retry attempts
   - Retry count stored in application_tracking
5. Audit trail maintained:
   - All status changes logged
   - Timestamp for each transition
   - Reason for status change
6. Queries supported:
   - Get all completed applications (last 7 days)
   - Get all pending applications
   - Get all failed applications with error details

### Technical Notes:
- Use database triggers or application code for audit logging
- Consider using state machine library (python-statemachine)
- Store confirmation details in JSON format
- Index on status and submitted_timestamp for fast queries

---

## Epic 4 Definition of Done

- [ ] Application Form Handler agent implemented
- [ ] Email submissions working (send to real test email)
- [ ] Simple web form submissions working (test on SEEK/Indeed sandbox)
- [ ] Complex forms detected and marked as pending
- [ ] Submission status accurately tracked in database
- [ ] End-to-end test: Job flows from "ready_to_send" → "completed"
- [ ] Confirmation emails/screenshots saved for audit
- [ ] Documentation: Submission flow and error handling guide
