"""
Fuzzy matching service for duplicate job detection.

Uses RapidFuzz algorithms to calculate similarity scores between job postings.
"""

from typing import Any

from loguru import logger
from rapidfuzz import fuzz


def normalize_string(text: str | None) -> str:
    """
    Normalize a string for consistent comparisons.

    Args:
        text: Input string to normalize

    Returns:
        Normalized lowercase string with whitespace stripped
    """
    if text is None:
        return ""

    # Convert to lowercase and strip extra whitespace
    normalized = text.lower().strip()

    # Replace multiple spaces with single space
    normalized = " ".join(normalized.split())

    return normalized


def location_normalize(location: str | None) -> str:
    """
    Normalize location strings for comparison.

    Handles variations in city/state formats, removes commas and extra spaces.

    Args:
        location: Location string to normalize

    Returns:
        Normalized location string
    """
    if location is None:
        return ""

    # Use basic normalization (lowercase, strip, collapse spaces)
    normalized = normalize_string(location)

    # Remove commas (common in "City, State" format)
    normalized = normalized.replace(",", "")

    # Collapse multiple spaces that might result from comma removal
    normalized = " ".join(normalized.split())

    return normalized


class FuzzyMatcher:
    """
    Fuzzy matching service for calculating job similarity.

    Uses RapidFuzz algorithms with weighted scoring:
    - Title: 20%
    - Company: 10%
    - Description: 50%
    - Location: 20%
    """

    def __init__(self):
        """Initialize fuzzy matcher."""
        self.title_weight = 0.20
        self.company_weight = 0.10
        self.description_weight = 0.50
        self.location_weight = 0.20

        logger.debug("FuzzyMatcher initialized with default weights")

    def title_similarity(self, title1: str | None, title2: str | None) -> float:
        """
        Calculate similarity between job titles using token_set_ratio.

        Token set ratio is ideal for titles as it handles word order variations.

        Args:
            title1: First job title
            title2: Second job title

        Returns:
            Similarity score from 0.0 to 1.0
        """
        if title1 is None or title2 is None:
            # If one is None and other is not, return 0
            if title1 != title2:
                return 0.0
            # If both None, return 1.0
            return 1.0

        norm1 = normalize_string(title1)
        norm2 = normalize_string(title2)

        if not norm1 and not norm2:
            return 1.0  # Both empty
        if not norm1 or not norm2:
            return 0.0  # One empty, one not

        # Use token_set_ratio for title matching (handles word order)
        score = fuzz.token_set_ratio(norm1, norm2)
        return score / 100.0

    def company_similarity(self, company1: str | None, company2: str | None) -> float:
        """
        Calculate similarity between company names.

        Args:
            company1: First company name
            company2: Second company name

        Returns:
            Similarity score from 0.0 to 1.0
        """
        if company1 is None or company2 is None:
            if company1 != company2:
                return 0.0
            return 1.0

        norm1 = normalize_string(company1)
        norm2 = normalize_string(company2)

        if not norm1 and not norm2:
            return 1.0
        if not norm1 or not norm2:
            return 0.0

        # Use basic ratio for company names
        score = fuzz.ratio(norm1, norm2)
        return score / 100.0

    def description_similarity(self, desc1: str | None, desc2: str | None) -> float:
        """
        Calculate similarity between job descriptions.

        Truncates to first 500 characters for performance.

        Args:
            desc1: First job description
            desc2: Second job description

        Returns:
            Similarity score from 0.0 to 1.0
        """
        if desc1 is None or desc2 is None:
            if desc1 != desc2:
                return 0.0
            return 1.0

        # Truncate to first 500 characters
        desc1_truncated = desc1[:500] if desc1 else ""
        desc2_truncated = desc2[:500] if desc2 else ""

        norm1 = normalize_string(desc1_truncated)
        norm2 = normalize_string(desc2_truncated)

        if not norm1 and not norm2:
            return 1.0
        if not norm1 or not norm2:
            return 0.0

        # Use token_set_ratio for descriptions (handles word order)
        score = fuzz.token_set_ratio(norm1, norm2)
        return score / 100.0

    def location_similarity(self, loc1: str | None, loc2: str | None) -> float:
        """
        Calculate similarity between locations.

        Handles format variations (e.g., "Sydney, NSW" vs "Sydney NSW").

        Args:
            loc1: First location
            loc2: Second location

        Returns:
            Similarity score from 0.0 to 1.0
        """
        if loc1 is None or loc2 is None:
            if loc1 != loc2:
                return 0.0
            return 1.0

        norm1 = location_normalize(loc1)
        norm2 = location_normalize(loc2)

        if not norm1 and not norm2:
            return 1.0
        if not norm1 or not norm2:
            return 0.0

        # Use ratio for normalized locations
        score = fuzz.ratio(norm1, norm2)
        return score / 100.0

    def weighted_similarity_score(self, job1: dict[str, Any], job2: dict[str, Any]) -> float:
        """
        Calculate weighted similarity score between two jobs.

        Weights:
        - Title: 20%
        - Company: 10%
        - Description: 50%
        - Location: 20%

        Args:
            job1: First job dictionary with keys: job_title, company_name, job_description, location
            job2: Second job dictionary with same keys

        Returns:
            Combined similarity score from 0.0 to 1.0
        """
        title_score = self.title_similarity(job1.get("job_title"), job2.get("job_title"))
        company_score = self.company_similarity(job1.get("company_name"), job2.get("company_name"))
        description_score = self.description_similarity(job1.get("job_description"), job2.get("job_description"))
        location_score = self.location_similarity(job1.get("location"), job2.get("location"))

        # Calculate weighted average
        weighted_score = title_score * self.title_weight + company_score * self.company_weight + description_score * self.description_weight + location_score * self.location_weight

        logger.debug(f"Similarity scores - Title: {title_score:.2f}, Company: {company_score:.2f}, Description: {description_score:.2f}, Location: {location_score:.2f}, Weighted: {weighted_score:.2f}")

        return weighted_score
