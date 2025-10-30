"""
Job Matcher Agent - Scores jobs against target criteria.

This agent evaluates discovered jobs against the user's search criteria
and determines which jobs should proceed through the application pipeline.
Uses Claude AI for intelligent matching with weighted scoring across:
- Must-have technologies (50%)
- Strong preference technologies (30%)
- Nice-to-have technologies (10%)
- Location match (10%)
"""

import json
import time
from pathlib import Path
from typing import Any

import yaml
from rapidfuzz import fuzz
from loguru import logger

from app.agents.base_agent import AgentResult, BaseAgent


class JobMatcherAgent(BaseAgent):
    """
    Agent that scores jobs against target criteria and approves/rejects them.

    Inherits from BaseAgent and implements the job matching logic using
    Claude AI for intelligent evaluation of job descriptions against
    candidate preferences.

    Attributes:
        _search_criteria: Cached search criteria from search.yaml
        _scoring_weights: Scoring weights from agents.yaml
        _match_threshold: Minimum score to approve job (default: 0.70)
    """

    def __init__(self, config: dict[str, Any], claude_client: Any, app_repository: Any):
        """
        Initialize Job Matcher Agent.

        Args:
            config: Agent-specific configuration from agents.yaml
            claude_client: Anthropic Claude API client
            app_repository: ApplicationRepository for database access
        """
        super().__init__(config, claude_client, app_repository)
        self._search_criteria: dict[str, Any] | None = None
        self._scoring_weights = config.get("scoring_weights", {"must_have_present": 0.50, "strong_preference_present": 0.30, "nice_to_have_present": 0.10, "location_match": 0.10})
        self._match_threshold = config.get("match_threshold", 0.70)

    @property
    def agent_name(self) -> str:
        """Return agent name."""
        return "job_matcher"

    async def process(self, job_id: str) -> AgentResult:
        """
        Process a job through the matching agent.

        Evaluates job against search criteria and returns match score
        and approval decision.

        Args:
            job_id: UUID of the job to process

        Returns:
            AgentResult with success status, match score, and approval decision
        """
        start_time = time.time()

        try:
            # Validate job_id
            if not job_id:
                logger.error("[job_matcher] Missing job_id parameter")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message="Missing job_id parameter", execution_time_ms=int((time.time() - start_time) * 1000))

            # Load job data from database
            logger.info(f"[job_matcher] Processing job: {job_id}")
            job_data = await self._app_repo.get_job_by_id(job_id)

            if not job_data:
                logger.error(f"[job_matcher] Job not found: {job_id}")
                return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=f"Job not found: {job_id}", execution_time_ms=int((time.time() - start_time) * 1000))

            # Load search criteria
            criteria = self._load_search_criteria()

            # Update current stage
            await self._update_current_stage(job_id, self.agent_name)

            # Call Claude to analyze job
            claude_response = await self._analyze_job_with_claude(job_data, criteria)

            # Parse Claude response
            parsed_response = self._parse_claude_response(claude_response)

            # Calculate scores
            must_have_score = self._calculate_must_have_score(criteria["must_have"], parsed_response["must_have_found"])

            strong_pref_score = self._calculate_component_score(criteria["strong_preference"], parsed_response["strong_pref_found"])

            nice_to_have_score = self._calculate_component_score(criteria["nice_to_have"], parsed_response["nice_to_have_found"])

            location_score = self._calculate_location_score(parsed_response["location_assessment"], criteria["primary_location"], criteria.get("acceptable_location", ""))

            # Calculate weighted final score
            final_score = self._calculate_final_score(must_have_score, strong_pref_score, nice_to_have_score, location_score)

            # Make approval decision
            approved = final_score >= self._match_threshold

            # Build output
            output = {
                "match_score": round(final_score, 3),
                "approved": approved,
                "must_have_found": parsed_response["must_have_found"],
                "must_have_missing": parsed_response.get("must_have_missing", []),
                "strong_pref_found": parsed_response["strong_pref_found"],
                "nice_to_have_found": parsed_response["nice_to_have_found"],
                "location_matched": parsed_response["location_assessment"],
                "scoring_breakdown": {"must_have_score": round(must_have_score, 3), "strong_pref_score": round(strong_pref_score, 3), "nice_to_have_score": round(nice_to_have_score, 3), "location_score": round(location_score, 3)},
                "reasoning": parsed_response.get("reasoning", ""),
            }

            # Update database
            new_status = "matched" if approved else "rejected"
            await self._update_status(job_id, new_status)
            await self._add_completed_stage(job_id, self.agent_name, output)

            # Log decision
            logger.info(f"[job_matcher] Job {job_id}: score={final_score:.3f}, approved={approved}, status={new_status}")

            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=True, agent_name=self.agent_name, output=output, error_message=None, execution_time_ms=execution_time_ms)

        except Exception as e:
            logger.error(f"[job_matcher] Error processing job {job_id}: {e}")
            execution_time_ms = int((time.time() - start_time) * 1000)

            return AgentResult(success=False, agent_name=self.agent_name, output={}, error_message=str(e), execution_time_ms=execution_time_ms)

    def _load_search_criteria(self) -> dict[str, Any]:
        """
        Load search criteria from search.yaml.

        Returns:
            Dictionary containing must_have, strong_preference, nice_to_have,
            primary_location, and acceptable_location
        """
        if self._search_criteria is not None:
            return self._search_criteria

        config_path = Path("config/search.yaml")

        try:
            with open(config_path) as f:
                search_config = yaml.safe_load(f)

            technologies = search_config.get("technologies", {})
            locations = search_config.get("locations", {})

            self._search_criteria = {
                "must_have": technologies.get("must_have", []),
                "strong_preference": technologies.get("strong_preference", []),
                "nice_to_have": technologies.get("nice_to_have", []),
                "primary_location": locations.get("primary", ""),
                "acceptable_location": locations.get("acceptable", ""),
            }

            logger.debug(f"[job_matcher] Loaded search criteria: {self._search_criteria}")
            return self._search_criteria

        except Exception as e:
            logger.error(f"[job_matcher] Failed to load search.yaml: {e}")
            raise

    async def _analyze_job_with_claude(self, job_data: dict[str, Any], criteria: dict[str, Any]) -> str:
        """
        Call Claude to analyze job against criteria.

        Args:
            job_data: Job information from database
            criteria: Search criteria with technology and location preferences

        Returns:
            Claude's JSON response as string
        """
        prompt = self._build_matching_prompt(job_data, criteria)

        system_prompt = """You are a Job Matcher Agent evaluating if a job matches a candidate's criteria.
Analyze the job description and identify which technologies are mentioned.
Consider variations and related technologies (e.g., "Spark", "PySpark", "Apache Spark").
Be case-insensitive in matching.
Return your analysis as valid JSON only, no additional text."""

        response = await self._call_claude(prompt, system_prompt)
        return response

    def _build_matching_prompt(self, job_data: dict[str, Any], criteria: dict[str, Any]) -> str:
        """
        Build prompt for Claude to analyze job matching.

        Args:
            job_data: Job information
            criteria: Search criteria

        Returns:
            Formatted prompt string
        """
        prompt = f"""JOB DETAILS:
- Title: {job_data.get("title", "N/A")}
- Company: {job_data.get("company_name", "N/A")}
- Description: {job_data.get("description", "N/A")}
- Location: {job_data.get("location", "N/A")}

CANDIDATE CRITERIA:
Must-Have Technologies (Required):
{", ".join(criteria["must_have"])}

Strong Preference Technologies (Highly Valued):
{", ".join(criteria["strong_preference"])}

Nice-to-Have Technologies (Bonus):
{", ".join(criteria["nice_to_have"])}

Location Preferences:
- Primary: {criteria["primary_location"]}
- Acceptable: {criteria.get("acceptable_location", "Not specified")}

TASK:
Analyze the job description and identify which technologies are mentioned.
For each technology category, list the technologies you found.
For location, determine if it matches "primary", "acceptable", or "no_match".

OUTPUT FORMAT (JSON only):
{{
  "must_have_found": ["Technology1", "Technology2"],
  "must_have_missing": ["MissingTech"],
  "strong_pref_found": ["Technology3"],
  "nice_to_have_found": ["Technology4"],
  "location_assessment": "primary|acceptable|no_match",
  "reasoning": "Brief explanation of the match assessment"
}}"""

        return prompt

    def _parse_claude_response(self, response: str) -> dict[str, Any]:
        """
        Parse Claude's JSON response.

        Args:
            response: JSON string from Claude

        Returns:
            Parsed dictionary with match data
        """
        try:
            # Extract JSON from response (Claude sometimes adds markdown)
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                response = response[start:end].strip()
            elif "```" in response:
                start = response.find("```") + 3
                end = response.find("```", start)
                response = response[start:end].strip()

            parsed = json.loads(response)
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"[job_matcher] Failed to parse Claude response: {e}")
            # Return empty match if parsing fails
            return {"must_have_found": [], "must_have_missing": [], "strong_pref_found": [], "nice_to_have_found": [], "location_assessment": "no_match", "reasoning": "Failed to parse matching results"}

    def _calculate_must_have_score(self, must_have_list: list[str], found: list[str]) -> float:
        """
        Calculate score for must-have technologies.

        Args:
            must_have_list: Required technologies
            found: Technologies found in job description

        Returns:
            Score between 0.0 and 1.0
        """
        if not must_have_list:
            return 1.0

        # Use fuzzy matching to find technologies
        matched_count = 0
        for required_tech in must_have_list:
            for found_tech in found:
                if self._is_fuzzy_match(required_tech, found_tech):
                    matched_count += 1
                    break

        score = matched_count / len(must_have_list)
        return score

    def _calculate_component_score(self, tech_list: list[str], found: list[str]) -> float:
        """
        Calculate score for a technology category (strong_pref or nice_to_have).

        Args:
            tech_list: Technologies in this category
            found: Technologies found in job description

        Returns:
            Score between 0.0 and 1.0
        """
        if not tech_list:
            return 1.0

        matched_count = 0
        for tech in tech_list:
            for found_tech in found:
                if self._is_fuzzy_match(tech, found_tech):
                    matched_count += 1
                    break

        score = matched_count / len(tech_list)
        return score

    def _calculate_location_score(self, location_assessment: str, primary_location: str, acceptable_location: str) -> float:
        """
        Calculate location match score.

        Args:
            location_assessment: Claude's assessment (primary/acceptable/no_match)
            primary_location: Primary location preference
            acceptable_location: Acceptable location alternative

        Returns:
            Score: 1.0 (primary), 0.5 (acceptable), 0.0 (no match)
        """
        if location_assessment == "primary":
            return 1.0
        elif location_assessment == "acceptable":
            return 0.5
        else:
            return 0.0

    def _calculate_final_score(self, must_have_score: float, strong_pref_score: float, nice_to_have_score: float, location_score: float) -> float:
        """
        Calculate weighted final score.

        Args:
            must_have_score: Score for must-have technologies
            strong_pref_score: Score for strong preference technologies
            nice_to_have_score: Score for nice-to-have technologies
            location_score: Score for location match

        Returns:
            Weighted final score between 0.0 and 1.0
        """
        weights = self._scoring_weights

        final_score = (
            must_have_score * weights.get("must_have_present", 0.50)
            + strong_pref_score * weights.get("strong_preference_present", 0.30)
            + nice_to_have_score * weights.get("nice_to_have_present", 0.10)
            + location_score * weights.get("location_match", 0.10)
        )

        # Ensure score is between 0.0 and 1.0
        final_score = max(0.0, min(1.0, final_score))

        return final_score

    def _normalize_tech_name(self, tech: str) -> str:
        """
        Normalize technology name for matching.

        Removes common prefixes and converts to lowercase.

        Args:
            tech: Technology name

        Returns:
            Normalized technology name
        """
        tech = tech.lower().strip()

        # Remove common prefixes
        prefixes = ["apache ", "aws ", "azure ", "google "]
        for prefix in prefixes:
            if tech.startswith(prefix):
                tech = tech[len(prefix) :]

        return tech

    def _is_fuzzy_match(self, tech1: str, tech2: str) -> bool:
        """
        Check if two technology names are fuzzy matches.

        Uses normalization and fuzzy string matching to handle
        variations in technology names.

        Args:
            tech1: First technology name
            tech2: Second technology name

        Returns:
            True if technologies are considered a match
        """
        norm1 = self._normalize_tech_name(tech1)
        norm2 = self._normalize_tech_name(tech2)

        # Direct match
        if norm1 == norm2:
            return True

        # Substring match (e.g., "spark" in "pyspark")
        if norm1 in norm2 or norm2 in norm1:
            return True

        # Fuzzy similarity match (threshold: 85%)
        similarity = fuzz.ratio(norm1, norm2)
        return similarity >= 85
