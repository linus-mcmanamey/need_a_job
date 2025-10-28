"""
Orchestrator Agent - Coordinates pipeline and makes application decisions.

Analyzes results from previous agents (JobMatcher, SalaryValidator, CVTailor,
CoverLetterWriter, QA) and makes decisions about job applications:
- auto_approve: Proceed to form submission
- needs_human_approval: Send to user for review
- auto_reject: Skip application
"""

import json
import time
from typing import Any

from loguru import logger

from app.agents.base_agent import AgentResult, BaseAgent

# Required stages that must be completed before orchestrator
REQUIRED_STAGES = ["job_matcher", "salary_validator", "cv_tailor", "cover_letter_writer", "qa"]

# Decision rules
AUTO_APPROVE_THRESHOLD = 85  # Match score >= 85% for auto-approve
NEEDS_APPROVAL_THRESHOLD = 60  # Match score >= 60% needs human approval
LOW_CONFIDENCE_THRESHOLD = 0.70  # Claude confidence < 70% needs human approval


class OrchestratorAgent(BaseAgent):
    """
    Agent that coordinates pipeline and makes job application decisions.

    Features:
    - Verifies all required stages completed
    - Analyzes previous agent results
    - Applies rule-based decision logic
    - Gets Claude decision support
    - Combines decisions for final recommendation
    - Updates application status appropriately
    - Implements human-in-the-loop pattern
    """

    @property
    def agent_name(self) -> str:
        """Return agent name."""
        return "orchestrator"

    async def process(self, job_id: str) -> AgentResult:
        """
        Process a job through orchestration decision logic.

        Args:
            job_id: UUID of the job to process

        Returns:
            AgentResult with success status, decision, reasoning
        """
        start_time = time.time()

        try:
            # Validate job_id
            if not job_id:
                logger.error("[orchestrator] Missing job_id parameter")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Missing job_id parameter", execution_time_ms=int((time.time() - start_time) * 1000))

            # Load job data
            logger.info(f"[orchestrator] Processing job: {job_id}")
            job_data = await self._app_repo.get_job_by_id(job_id)

            if not job_data:
                logger.error(f"[orchestrator] Job not found: {job_id}")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Job not found: {job_id}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Update current stage
            await self._update_current_stage(job_id, self.agent_name)

            # Load stage outputs
            stage_outputs = await self._app_repo.get_stage_outputs(job_id)

            # Verify all required stages completed
            if not self._verify_required_stages(stage_outputs):
                logger.error(f"[orchestrator] Job {job_id}: Not all required stages completed")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Not all required stages completed. Cannot make decision.", execution_time_ms=int((time.time() - start_time) * 1000))

            # Extract key metrics
            metrics = self._extract_metrics(stage_outputs)

            # Apply rule-based decision logic
            rule_decision = self._apply_decision_rules(metrics)
            logger.debug(f"[orchestrator] Rule-based decision: {rule_decision} (metrics={metrics})")

            # Get Claude recommendation
            claude_rec = await self._get_claude_recommendation(job_data, stage_outputs)
            logger.debug(f"[orchestrator] Claude recommendation: {claude_rec}")

            # Combine decisions
            final_decision = self._combine_decisions(rule_decision, claude_rec)
            logger.info(f"[orchestrator] Final decision for job {job_id}: {final_decision}")

            # Generate reasoning
            reasoning = self._generate_reasoning(final_decision, metrics, claude_rec)

            # Build output
            output = {
                "decision": final_decision,
                "reasoning": reasoning,
                "confidence": claude_rec.get("confidence", 0.80),
                "match_score": metrics["match_score"],
                "salary_passed": metrics["salary_passed"],
                "qa_passed": metrics["qa_passed"],
                "flagged_concerns": claude_rec.get("flagged_concerns", []),
                "recommended_action": self._decision_to_action(final_decision),
            }

            # Update database
            await self._update_database(job_id, output)
            await self._add_completed_stage(job_id, self.agent_name, output)

            logger.info(f"[orchestrator] Job {job_id}: Decision={final_decision}, Action={output['recommended_action']}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=True, agent_name=self.agent_name, output=output, error_message=None, execution_time_ms=execution_time_ms)

        except Exception as e:
            logger.error(f"[orchestrator] Error processing job {job_id}: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=str(e), execution_time_ms=execution_time_ms)

    def _verify_required_stages(self, stage_outputs: dict[str, Any]) -> bool:
        """
        Verify all required pipeline stages have been completed.

        Args:
            stage_outputs: Dictionary of stage outputs from previous agents

        Returns:
            True if all required stages completed, False otherwise
        """
        for stage in REQUIRED_STAGES:
            if stage not in stage_outputs or not stage_outputs[stage]:
                logger.warning(f"[orchestrator] Missing required stage: {stage}")
                return False
        return True

    def _extract_metrics(self, stage_outputs: dict[str, Any]) -> dict[str, Any]:
        """
        Extract key metrics from previous agent outputs.

        Args:
            stage_outputs: Dictionary of stage outputs

        Returns:
            Dictionary of extracted metrics
        """
        metrics = {"match_score": stage_outputs.get("job_matcher", {}).get("match_score", 0.0), "salary_passed": stage_outputs.get("salary_validator", {}).get("passed", False), "qa_passed": stage_outputs.get("qa", {}).get("pass", False)}

        # Check for warnings in salary validator
        salary_output = stage_outputs.get("salary_validator", {})
        if "warnings" in salary_output and salary_output["warnings"]:
            metrics["salary_has_warnings"] = True

        # Check for warnings in QA
        qa_output = stage_outputs.get("qa", {})
        if "issues" in qa_output:
            # Check if there are warning-level issues
            warning_issues = [i for i in qa_output["issues"] if i.get("severity") == "warning"]
            if warning_issues:
                metrics["qa_has_warnings"] = True

        return metrics

    def _apply_decision_rules(self, metrics: dict[str, Any]) -> str:
        """
        Apply rule-based decision logic.

        Decision rules:
        - auto_approve: Match >= 85%, salary passed, QA passed, no warnings
        - auto_reject: Match < 60% OR salary failed OR QA failed
        - needs_human_approval: Everything else (60-84% match OR has warnings)

        Args:
            metrics: Extracted metrics from previous stages

        Returns:
            Decision string: auto_approve, needs_human_approval, or auto_reject
        """
        match_score = metrics["match_score"]
        salary_passed = metrics["salary_passed"]
        qa_passed = metrics["qa_passed"]
        has_warnings = metrics.get("salary_has_warnings", False) or metrics.get("qa_has_warnings", False)

        # Auto-reject criteria
        if match_score < NEEDS_APPROVAL_THRESHOLD:
            return "auto_reject"
        if not salary_passed:
            return "auto_reject"
        if not qa_passed:
            return "auto_reject"

        # Auto-approve criteria (high match, all passed, no warnings)
        if match_score >= AUTO_APPROVE_THRESHOLD and salary_passed and qa_passed and not has_warnings:
            return "auto_approve"

        # Default to human approval for medium match or warnings
        return "needs_human_approval"

    async def _get_claude_recommendation(self, job_data: dict[str, Any], stage_outputs: dict[str, Any]) -> dict[str, Any]:
        """
        Get Claude decision support recommendation.

        Args:
            job_data: Job information
            stage_outputs: Previous agent outputs

        Returns:
            Dictionary with recommended_decision, reasoning, confidence, flagged_concerns
        """
        # Extract key information
        job_title = job_data.get("title", "Unknown")
        company_name = job_data.get("company_name", "Unknown")
        location = job_data.get("location", "Unknown")
        salary_range = job_data.get("salary_range", "Not specified")

        match_output = stage_outputs.get("job_matcher", {})
        salary_output = stage_outputs.get("salary_validator", {})
        qa_output = stage_outputs.get("qa", {})

        match_score = match_output.get("match_score", 0)
        match_reasoning = match_output.get("reasoning", "No reasoning provided")

        salary_status = "Passed" if salary_output.get("passed") else "Failed"
        salary_analysis = salary_output.get("analysis", "No analysis")

        qa_status = "Passed" if qa_output.get("pass") else "Failed"
        qa_issues = qa_output.get("issues", [])

        prompt = f"""You are an Orchestrator Agent making decisions about job applications. Analyze the following job application data and recommend whether to approve, request human review, or reject.

JOB DETAILS:
Title: {job_title}
Company: {company_name}
Location: {location}
Salary: {salary_range}

MATCH ANALYSIS (JobMatcher):
Match Score: {match_score}%
Reasoning: {match_reasoning}

SALARY ANALYSIS (SalaryValidator):
Status: {salary_status}
Analysis: {salary_analysis}

QUALITY ASSURANCE (QA):
Status: {qa_status}
Issues Found: {len(qa_issues)}

DECISION CRITERIA:
- Auto-Approve: Match ≥85%, Salary passed, QA passed, no warnings
- Human Review: Match 60-84%, OR has warnings, OR unique characteristics
- Auto-Reject: Match <60%, OR Salary failed, OR QA failed

TASK:
Recommend a decision and provide clear reasoning. Consider:
1. Job quality and fit for candidate
2. Validation results from previous agents
3. Any red flags or concerns
4. Likelihood of application success

OUTPUT FORMAT (JSON only):
{{
  "recommended_decision": "auto_approve|needs_human_approval|auto_reject",
  "reasoning": "Clear explanation of recommendation",
  "confidence": 0.85,
  "flagged_concerns": ["concern 1", "concern 2"]
}}"""

        system_prompt = "You are an expert orchestrator making data-driven decisions about job applications. Analyze all available data and provide a well-reasoned recommendation. Output valid JSON only."

        try:
            response = await self._call_claude(prompt, system_prompt)
            logger.debug(f"[orchestrator] Claude response: {len(response)} chars")

            # Parse JSON response
            result = json.loads(response)
            return result
        except json.JSONDecodeError as e:
            logger.error(f"[orchestrator] Failed to parse Claude JSON response: {e}")
            # Fallback to safe default
            return {"recommended_decision": "needs_human_approval", "reasoning": "Unable to get AI recommendation, defaulting to human review", "confidence": 0.50, "flagged_concerns": ["AI recommendation unavailable"]}
        except Exception as e:
            logger.error(f"[orchestrator] Claude API error: {e}")
            # Fallback to safe default
            return {"recommended_decision": "needs_human_approval", "reasoning": "Error getting AI recommendation, defaulting to human review", "confidence": 0.50, "flagged_concerns": ["API error occurred"]}

    def _combine_decisions(self, rule_decision: str, claude_rec: dict[str, Any]) -> str:
        """
        Combine rule-based and Claude decisions into final decision.

        Strategy:
        - If both agree: use that decision
        - If conflict: defer to human (needs_human_approval)
        - If Claude low confidence (<70%): defer to human

        Args:
            rule_decision: Decision from rule-based logic
            claude_rec: Claude recommendation dict

        Returns:
            Final decision string
        """
        claude_decision = claude_rec.get("recommended_decision", "needs_human_approval")
        confidence = claude_rec.get("confidence", 0.50)

        # Low confidence: defer to human
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            logger.debug(f"[orchestrator] Low Claude confidence ({confidence}), deferring to human")
            return "needs_human_approval"

        # Both agree: use that decision
        if rule_decision == claude_decision:
            logger.debug(f"[orchestrator] Rule and Claude agree: {rule_decision} (confidence={confidence})")
            return rule_decision

        # Conflict: defer to human for safety
        logger.debug(f"[orchestrator] Conflict - Rule: {rule_decision}, Claude: {claude_decision}, deferring to human")
        return "needs_human_approval"

    def _generate_reasoning(self, decision: str, metrics: dict[str, Any], claude_rec: dict[str, Any] | None = None) -> str:
        """
        Generate human-readable reasoning for the decision.

        Args:
            decision: Final decision
            metrics: Extracted metrics
            claude_rec: Claude recommendation (optional)

        Returns:
            Reasoning string
        """
        match_score = metrics["match_score"]
        salary_passed = metrics["salary_passed"]
        qa_passed = metrics["qa_passed"]

        # Base reasoning on decision type
        if decision == "auto_approve":
            reasoning = f"Auto-approved: High match score ({match_score}%), salary validation passed, QA passed with no critical issues."
        elif decision == "auto_reject":
            if match_score < NEEDS_APPROVAL_THRESHOLD:
                reasoning = f"Auto-rejected: Low match score ({match_score}% < {NEEDS_APPROVAL_THRESHOLD}% threshold)."
            elif not salary_passed:
                reasoning = "Auto-rejected: Salary validation failed."
            elif not qa_passed:
                reasoning = "Auto-rejected: Quality assurance failed."
            else:
                reasoning = "Auto-rejected: Failed validation criteria."
        else:  # needs_human_approval
            reasoning = f"Human review required: Match score {match_score}% (moderate fit)"
            if metrics.get("salary_has_warnings"):
                reasoning += ", salary has warnings"
            if metrics.get("qa_has_warnings"):
                reasoning += ", QA has warnings"
            reasoning += "."

        # Append Claude reasoning if available
        if claude_rec and "reasoning" in claude_rec:
            claude_reasoning = claude_rec["reasoning"]
            reasoning += f" AI analysis: {claude_reasoning}"

        return reasoning

    async def _update_database(self, job_id: str, output: dict[str, Any]) -> None:
        """
        Update database based on orchestrator decision.

        Args:
            job_id: Job ID
            output: Decision output dict
        """
        decision = output["decision"]

        # Map decision to status
        status_map = {"auto_approve": "approved", "needs_human_approval": "pending_approval", "auto_reject": "rejected"}

        new_status = status_map.get(decision, "pending")

        # Update application status
        if hasattr(self._app_repo, "update_status"):
            await self._app_repo.update_status(job_id, new_status)
            logger.debug(f"[orchestrator] Updated job {job_id} status to {new_status}")

    def _decision_to_action(self, decision: str) -> str:
        """
        Convert decision to recommended action.

        Args:
            decision: Decision string

        Returns:
            Action string: apply, review, or skip
        """
        action_map = {"auto_approve": "apply", "needs_human_approval": "review", "auto_reject": "skip"}
        return action_map.get(decision, "review")
