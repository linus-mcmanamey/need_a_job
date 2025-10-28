"""
QA Agent - Validates generated CV and CL for quality and accuracy.

Performs quality checks on generated documents including Australian English
verification, formatting consistency, fabrication detection, and contact
information accuracy.
"""

import json
import re
import time
from pathlib import Path
from typing import Any

from docx import Document
from loguru import logger

from app.agents.base_agent import AgentResult, BaseAgent

# Australian vs American spelling mappings
AUSTRALIAN_VS_AMERICAN = {
    "color": "colour",
    "center": "centre",
    "organization": "organisation",
    "organize": "organise",
    "recognize": "recognise",
    "realize": "realise",
    "analyze": "analyse",
    "specialized": "specialised",
    "optimized": "optimised",
    "optimize": "optimise",
    "specialize": "specialise",
    "behavior": "behaviour",
    "defense": "defence",
    "license": "licence",
    "program": "programme",  # Note: "program" (computer) is acceptable, but "programme" (TV) in some contexts
}


class QAAgent(BaseAgent):
    """
    Agent that validates generated CV and CL for quality and accuracy.

    Features:
    - Loads generated and original documents
    - Checks Australian English spelling
    - Detects formatting issues
    - Identifies potential fabrication
    - Validates contact information
    - Uses Claude for comprehensive quality analysis
    - Generates pass/fail report with issues list
    """

    def __init__(self, config: dict[str, Any], claude_client: Any, app_repository: Any):
        """Initialize QA Agent."""
        super().__init__(config, claude_client, app_repository)
        self._cv_template_path = Path("current_cv_coverletter/Linus_McManamey_CV.docx")
        self._cl_template_path = Path("current_cv_coverletter/Linus_McManamey_CL.docx")

    @property
    def agent_name(self) -> str:
        """Return agent name."""
        return "qa"

    async def process(self, job_id: str) -> AgentResult:
        """
        Process a job through QA validation.

        Args:
            job_id: UUID of the job to process

        Returns:
            AgentResult with success status, QA report, issues list
        """
        start_time = time.time()

        try:
            # Validate job_id
            if not job_id:
                logger.error("[qa] Missing job_id parameter")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Missing job_id parameter", execution_time_ms=int((time.time() - start_time) * 1000))

            # Load job data
            logger.info(f"[qa] Processing job: {job_id}")
            job_data = await self._app_repo.get_job_by_id(job_id)

            if not job_data:
                logger.error(f"[qa] Job not found: {job_id}")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Job not found: {job_id}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Update current stage
            await self._update_current_stage(job_id, self.agent_name)

            # Load stage outputs
            stage_outputs = await self._app_repo.get_stage_outputs(job_id)

            # Get file paths
            cv_file_path = stage_outputs.get("cv_tailor", {}).get("cv_file_path")
            cl_file_path = stage_outputs.get("cover_letter_writer", {}).get("cl_file_path")

            if not cv_file_path:
                logger.error("[qa] CV file path not found in stage outputs")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="CV file path not found in stage outputs", execution_time_ms=int((time.time() - start_time) * 1000))

            if not cl_file_path:
                logger.error("[qa] CL file path not found in stage outputs")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="CL file path not found in stage outputs", execution_time_ms=int((time.time() - start_time) * 1000))

            # Load documents
            try:
                original_cv_doc = self._load_document(self._cv_template_path)
                original_cl_doc = self._load_document(self._cl_template_path)
                generated_cv_doc = self._load_document(Path(cv_file_path))
                generated_cl_doc = self._load_document(Path(cl_file_path))
            except FileNotFoundError as e:
                logger.error(f"[qa] Document not found: {e}")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Document not found: {e}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Extract text from documents
            original_cv_text = self._extract_text_from_document(original_cv_doc)
            original_cl_text = self._extract_text_from_document(original_cl_doc)
            generated_cv_text = self._extract_text_from_document(generated_cv_doc)
            generated_cl_text = self._extract_text_from_document(generated_cl_doc)

            # Perform quality checks
            spelling_issues_cv = self._check_australian_english(generated_cv_text)
            spelling_issues_cl = self._check_australian_english(generated_cl_text)

            fabrication_issues_cv = self._check_fabrication(original_cv_text, generated_cv_text, "CV")
            fabrication_issues_cl = self._check_fabrication(original_cl_text, generated_cl_text, "CL")

            contact_issues = self._check_contact_info(original_cv_text, generated_cv_text)

            # Use Claude for comprehensive analysis
            claude_analysis = await self._analyze_with_claude(original_cv_text, generated_cv_text, original_cl_text, generated_cl_text)

            # Aggregate all issues
            all_issues = self._aggregate_issues(spelling_issues_cv + spelling_issues_cl, fabrication_issues_cv + fabrication_issues_cl, contact_issues, claude_analysis.get("issues", []))

            # Make pass/fail decision
            passed = self._should_pass(all_issues)

            # Build output
            output = {"pass": passed, "issues": all_issues, "checked_cv": True, "checked_cl": True, "recommendations": claude_analysis.get("recommendations", [])}

            # Update database
            if passed:
                if hasattr(self._app_repo, "update_status"):
                    await self._app_repo.update_status(job_id, "documents_generated")
            else:
                if hasattr(self._app_repo, "update_status"):
                    await self._app_repo.update_status(job_id, "pending")

            await self._add_completed_stage(job_id, self.agent_name, output)

            logger.info(f"[qa] Job {job_id}: QA {'PASSED' if passed else 'FAILED'}, issues={len(all_issues)}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=passed, agent_name=self.agent_name, output=output, error_message=None if passed else "QA failed with critical issues", execution_time_ms=execution_time_ms)

        except Exception as e:
            logger.error(f"[qa] Error processing job {job_id}: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=str(e), execution_time_ms=execution_time_ms)

    def _load_document(self, doc_path: Path) -> Document:
        """Load document from DOCX file."""
        if not doc_path.exists():
            raise FileNotFoundError(f"Document not found: {doc_path}")

        try:
            doc = Document(doc_path)
            logger.debug(f"[qa] Loaded document: {doc_path}")
            return doc
        except Exception as e:
            logger.error(f"[qa] Failed to parse document: {e}")
            raise

    def _extract_text_from_document(self, doc: Document) -> str:
        """Extract plain text from DOCX document."""
        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)
        return "\n".join(text_parts)

    def _check_australian_english(self, text: str) -> list[dict[str, Any]]:
        """Check for American vs Australian spelling."""
        issues = []
        for american, australian in AUSTRALIAN_VS_AMERICAN.items():
            # Case-insensitive word boundary search
            pattern = rf"\b{american}\b"
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                issues.append({"type": "spelling", "description": f"American spelling '{match.group()}' should be '{australian}'", "severity": "critical", "location": "document"})
        return issues

    def _check_fabrication(self, original_text: str, generated_text: str, doc_type: str) -> list[dict[str, Any]]:
        """Check for potential fabrication (content not in original)."""
        issues = []

        # Simple word-based check for new content
        # Extract meaningful words (3+ chars, not common words)
        common_words = {"and", "the", "for", "with", "from", "that", "this", "have", "been", "will", "can", "are", "was", "were", "has", "had"}

        original_words = set(re.findall(r"\b\w{3,}\b", original_text.lower()))
        generated_words = set(re.findall(r"\b\w{3,}\b", generated_text.lower()))

        # Remove common words
        original_words -= common_words
        generated_words -= common_words

        # Find words in generated that aren't in original
        new_words = generated_words - original_words

        # Flag if significant new content (more than 10 new words)
        if len(new_words) > 10:
            sample_words = list(new_words)[:5]
            issues.append({"type": "fabrication", "description": f"Potential new content in {doc_type}: {', '.join(sample_words)}...", "severity": "warning", "location": doc_type})

        return issues

    def _check_contact_info(self, original_text: str, generated_text: str) -> list[dict[str, Any]]:
        """Check contact information accuracy."""
        issues = []

        # Extract email addresses
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        original_emails = set(re.findall(email_pattern, original_text))
        generated_emails = set(re.findall(email_pattern, generated_text))

        # Check if emails match
        if original_emails != generated_emails:
            missing = original_emails - generated_emails
            extra = generated_emails - original_emails
            if missing:
                issues.append({"type": "contact_info", "description": f"Missing email(s): {', '.join(missing)}", "severity": "critical", "location": "contact information"})
            if extra:
                issues.append({"type": "contact_info", "description": f"Extra/incorrect email(s): {', '.join(extra)}", "severity": "critical", "location": "contact information"})

        # Extract phone numbers (Australian format)
        phone_pattern = r"\+?61\s?[2-4]\d{2}\s?\d{3}\s?\d{3}|\(\d{2}\)\s?\d{4}\s?\d{4}|04\d{2}\s?\d{3}\s?\d{3}"
        original_phones = set(re.findall(phone_pattern, original_text))
        generated_phones = set(re.findall(phone_pattern, generated_text))

        if original_phones != generated_phones:
            if original_phones - generated_phones:
                issues.append({"type": "contact_info", "description": "Phone number mismatch", "severity": "critical", "location": "contact information"})

        return issues

    async def _analyze_with_claude(self, original_cv: str, generated_cv: str, original_cl: str, generated_cl: str) -> dict[str, Any]:
        """Use Claude for comprehensive quality analysis."""
        prompt = f"""You are a Quality Assurance Agent for job application documents. Analyze the generated CV and Cover Letter for quality and accuracy.

ORIGINAL CV CONTENT (first 1000 chars):
{original_cv[:1000]}

GENERATED CV CONTENT (first 1000 chars):
{generated_cv[:1000]}

ORIGINAL CL CONTENT (first 500 chars):
{original_cl[:500]}

GENERATED CL CONTENT (first 500 chars):
{generated_cl[:500]}

QUALITY CHECKS:
1. **Australian English:** Verify spelling (colour, centre, organisation, recognise, analyse)
2. **Formatting:** Check fonts, spacing, alignment, professional appearance
3. **No Fabrication:** Ensure no skills, experiences, or qualifications added that weren't in original
4. **Contact Information:** Verify name, email, phone match original

TASK:
Analyze the documents and identify any issues. For each issue, provide:
- Type: spelling | grammar | formatting | fabrication | contact_info
- Description: Clear explanation
- Severity: critical | warning | info
- Location: Where the issue occurs

OUTPUT FORMAT (JSON only):
{{
  "issues": [
    {{
      "type": "spelling",
      "description": "Issue description",
      "severity": "critical",
      "location": "CV page 1"
    }}
  ],
  "recommendations": ["Recommendation 1", "Recommendation 2"]
}}"""

        system_prompt = "You are a quality assurance expert for job application documents. Analyze documents for quality, accuracy, and compliance with Australian English standards. Output valid JSON only."

        try:
            response = await self._call_claude(prompt, system_prompt)
            logger.debug(f"[qa] Claude analysis response: {len(response)} chars")

            # Parse JSON response
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"[qa] Failed to parse Claude JSON response: {e}")
            return {"issues": [], "recommendations": []}
        except Exception as e:
            logger.error(f"[qa] Claude API error: {e}")
            return {"issues": [], "recommendations": []}

    def _aggregate_issues(self, *issue_lists: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Aggregate issues from multiple sources."""
        all_issues = []
        for issue_list in issue_lists:
            all_issues.extend(issue_list)
        return all_issues

    def _should_pass(self, issues: list[dict[str, Any]]) -> bool:
        """Determine if QA should pass based on issues."""
        # Fail if any critical issues
        critical_issues = [i for i in issues if i.get("severity") == "critical"]
        return len(critical_issues) == 0
