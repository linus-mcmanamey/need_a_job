"""
Duplicate detection service for identifying duplicate job postings.

Uses fuzzy matching to classify job similarity and group duplicates.
"""

from enum import Enum

from loguru import logger

from app.models.job import Job
from app.repositories.jobs_repository import JobsRepository
from app.services.fuzzy_matcher import FuzzyMatcher


class DuplicateClassification(Enum):
    """Classification types for duplicate detection."""

    DUPLICATE = "duplicate"  # ≥90% similarity - auto-group
    ANALYZE = "analyze"  # 75-89% similarity - flag for Tier 2
    DIFFERENT = "different"  # <75% similarity - different jobs


class DuplicateDetector:
    """
    Duplicate detection service using fuzzy matching.

    Identifies duplicate job postings across platforms using weighted similarity scoring.
    """

    def __init__(self, duplicate_threshold: float = 0.90, analyze_threshold: float = 0.75, days_lookback: int = 30):
        """
        Initialize duplicate detector.

        Args:
            duplicate_threshold: Threshold for auto-grouping duplicates (default 0.90)
            analyze_threshold: Threshold for flagging for deeper analysis (default 0.75)
            days_lookback: Days to look back for comparison (default 30)
        """
        self.jobs_repo = JobsRepository()
        self.fuzzy_matcher = FuzzyMatcher()

        self.duplicate_threshold = duplicate_threshold
        self.analyze_threshold = analyze_threshold
        self.days_lookback = days_lookback

        logger.info(f"DuplicateDetector initialized: duplicate_threshold={duplicate_threshold}, analyze_threshold={analyze_threshold}, days_lookback={days_lookback}")

    def _classify_similarity(self, similarity_score: float) -> DuplicateClassification:
        """
        Classify similarity score into duplicate, analyze, or different.

        Args:
            similarity_score: Similarity score from 0.0 to 1.0

        Returns:
            DuplicateClassification enum value
        """
        if similarity_score >= self.duplicate_threshold:
            return DuplicateClassification.DUPLICATE
        elif similarity_score >= self.analyze_threshold:
            return DuplicateClassification.ANALYZE
        else:
            return DuplicateClassification.DIFFERENT

    def _get_candidate_jobs(self, target_job: Job) -> list[Job]:
        """
        Get candidate jobs for comparison (pre-filtered by title keywords).

        Args:
            target_job: Job to find duplicates for

        Returns:
            List of candidate jobs for comparison
        """
        # Extract keywords from title (simple word extraction)
        title_words = target_job.job_title.lower().split()

        # Filter out common words
        common_words = {"the", "a", "an", "and", "or", "for", "in", "at", "to", "of", "with", "as"}
        keywords = [word for word in title_words if word not in common_words and len(word) > 2]

        # If no keywords, use first two words
        if not keywords:
            keywords = title_words[:2]

        # Get recent jobs matching keywords
        candidates = self.jobs_repo.get_recent_jobs_by_title(keywords, self.days_lookback)

        # Filter out the target job itself and jobs with same URL
        filtered_candidates = [job for job in candidates if job.job_id != target_job.job_id and job.job_url != target_job.job_url]

        logger.debug(f"Found {len(filtered_candidates)} candidate jobs for comparison (from {len(candidates)} total recent jobs)")

        return filtered_candidates

    def find_duplicates(self, job_id: str) -> dict:
        """
        Find duplicate jobs for a given job.

        Args:
            job_id: ID of the job to check for duplicates

        Returns:
            Dictionary with keys:
                - job_id: The target job ID
                - duplicates: List of dicts with job_id, similarity_score, classification
                - analyze: List of dicts with job_id, similarity_score, classification

        Raises:
            ValueError: If job not found
        """
        # Get target job
        target_job = self.jobs_repo.get_job_by_id(job_id)
        if not target_job:
            raise ValueError(f"Job not found: {job_id}")

        logger.info(f"Finding duplicates for job {job_id}: {target_job.job_title}")

        # Get candidate jobs
        candidates = self._get_candidate_jobs(target_job)

        duplicates = []
        analyze = []

        # Convert target job to dict for fuzzy matching
        target_dict = {"job_title": target_job.job_title, "company_name": target_job.company_name, "job_description": target_job.job_description, "location": target_job.location}

        # Compare with each candidate
        for candidate in candidates:
            candidate_dict = {"job_title": candidate.job_title, "company_name": candidate.company_name, "job_description": candidate.job_description, "location": candidate.location}

            # Calculate similarity
            similarity_score = self.fuzzy_matcher.weighted_similarity_score(target_dict, candidate_dict)

            # Classify
            classification = self._classify_similarity(similarity_score)

            result = {
                "job_id": candidate.job_id,
                "job_title": candidate.job_title,
                "company_name": candidate.company_name,
                "platform_source": candidate.platform_source,
                "similarity_score": similarity_score,
                "classification": classification.value,
            }

            if classification == DuplicateClassification.DUPLICATE:
                duplicates.append(result)
                logger.info(f"DUPLICATE: {candidate.job_id} - {candidate.job_title} (score: {similarity_score:.2f})")
            elif classification == DuplicateClassification.ANALYZE:
                analyze.append(result)
                logger.info(f"ANALYZE: {candidate.job_id} - {candidate.job_title} (score: {similarity_score:.2f})")
            else:
                logger.debug(f"DIFFERENT: {candidate.job_id} - {candidate.job_title} (score: {similarity_score:.2f})")

        logger.info(f"Duplicate detection complete for {job_id}: {len(duplicates)} duplicates, {len(analyze)} to analyze")

        return {"job_id": job_id, "duplicates": duplicates, "analyze": analyze}
