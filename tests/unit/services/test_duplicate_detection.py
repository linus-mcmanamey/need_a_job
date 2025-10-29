"""
Unit tests for duplicate detection service.

Tests business logic for finding duplicates, classification, and grouping.
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models.job import Job
from app.services.duplicate_detector import DuplicateClassification, DuplicateDetector


class TestDuplicateClassification:
    """Test DuplicateClassification enum."""

    def test_classification_values(self):
        """Test classification enum values."""
        assert DuplicateClassification.DUPLICATE.value == "duplicate"
        assert DuplicateClassification.ANALYZE.value == "analyze"
        assert DuplicateClassification.DIFFERENT.value == "different"


class TestDuplicateDetector:
    """Test DuplicateDetector class."""

    @pytest.fixture
    def mock_jobs_repo(self):
        """Create a mock jobs repository."""
        return MagicMock()

    @pytest.fixture
    def mock_fuzzy_matcher(self):
        """Create a mock fuzzy matcher."""
        return MagicMock()

    @pytest.fixture
    def detector(self, mock_jobs_repo, mock_fuzzy_matcher):
        """Create a DuplicateDetector instance with mocked dependencies."""
        with patch("app.services.duplicate_detector.JobsRepository", return_value=mock_jobs_repo):
            with patch("app.services.duplicate_detector.FuzzyMatcher", return_value=mock_fuzzy_matcher):
                return DuplicateDetector()

    def test_init(self, detector):
        """Test detector initialization."""
        assert detector is not None
        assert detector.duplicate_threshold == 0.90
        assert detector.analyze_threshold == 0.75
        assert detector.days_lookback == 30

    def test_get_candidate_jobs_basic(self, detector, mock_jobs_repo):
        """Test getting candidate jobs for comparison."""
        target_job = Job(job_id="job-1", job_title="Senior Python Developer", company_name="TechCorp", job_url="https://example.com/job1", platform_source="seek", discovered_timestamp=datetime.now())

        candidate_jobs = [
            Job(job_id="job-2", job_title="Python Developer Senior", company_name="TechCorp", job_url="https://example.com/job2", platform_source="indeed", discovered_timestamp=datetime.now() - timedelta(days=5)),
            Job(job_id="job-3", job_title="Senior Python Engineer", company_name="TechCorp", job_url="https://example.com/job3", platform_source="linkedin", discovered_timestamp=datetime.now() - timedelta(days=10)),
        ]

        mock_jobs_repo.get_recent_jobs_by_title = MagicMock(return_value=candidate_jobs)

        result = detector._get_candidate_jobs(target_job)

        assert len(result) == 2
        assert all(job.job_id != target_job.job_id for job in result)
        mock_jobs_repo.get_recent_jobs_by_title.assert_called_once()

    def test_get_candidate_jobs_excludes_same_url(self, detector, mock_jobs_repo):
        """Test that candidate jobs with same URL are excluded."""
        target_job = Job(job_id="job-1", job_title="Senior Python Developer", company_name="TechCorp", job_url="https://example.com/job1", platform_source="seek", discovered_timestamp=datetime.now())

        candidate_jobs = [
            Job(
                job_id="job-2",
                job_title="Senior Python Developer",
                company_name="TechCorp",
                job_url="https://example.com/job1",  # Same URL
                platform_source="indeed",
                discovered_timestamp=datetime.now() - timedelta(days=5),
            )
        ]

        mock_jobs_repo.get_recent_jobs_by_title = MagicMock(return_value=candidate_jobs)

        result = detector._get_candidate_jobs(target_job)

        # Should exclude job with same URL
        assert len(result) == 0

    def test_classify_similarity_duplicate(self, detector):
        """Test classification for duplicate threshold (≥90%)."""
        classification = detector._classify_similarity(0.95)
        assert classification == DuplicateClassification.DUPLICATE

        classification = detector._classify_similarity(0.90)
        assert classification == DuplicateClassification.DUPLICATE

    def test_classify_similarity_analyze(self, detector):
        """Test classification for analyze threshold (75-89%)."""
        classification = detector._classify_similarity(0.85)
        assert classification == DuplicateClassification.ANALYZE

        classification = detector._classify_similarity(0.75)
        assert classification == DuplicateClassification.ANALYZE

        classification = detector._classify_similarity(0.89)
        assert classification == DuplicateClassification.ANALYZE

    def test_classify_similarity_different(self, detector):
        """Test classification for different jobs (<75%)."""
        classification = detector._classify_similarity(0.74)
        assert classification == DuplicateClassification.DIFFERENT

        classification = detector._classify_similarity(0.50)
        assert classification == DuplicateClassification.DIFFERENT

        classification = detector._classify_similarity(0.0)
        assert classification == DuplicateClassification.DIFFERENT

    def test_find_duplicates_no_candidates(self, detector, mock_jobs_repo):
        """Test finding duplicates when no candidates exist."""
        target_job = Job(job_id="job-1", job_title="Senior Python Developer", company_name="TechCorp", job_url="https://example.com/job1", platform_source="seek")

        mock_jobs_repo.get_job_by_id = MagicMock(return_value=target_job)
        mock_jobs_repo.get_recent_jobs_by_title = MagicMock(return_value=[])

        result = detector.find_duplicates("job-1")

        assert result["duplicates"] == []
        assert result["analyze"] == []
        assert result["job_id"] == "job-1"

    def test_find_duplicates_with_duplicates(self, detector, mock_jobs_repo, mock_fuzzy_matcher):
        """Test finding duplicates when duplicates exist."""
        target_job = Job(job_id="job-1", job_title="Senior Python Developer", company_name="TechCorp", job_url="https://example.com/job1", platform_source="seek", job_description="Python developer needed", location="Sydney, NSW")

        duplicate_job = Job(
            job_id="job-2",
            job_title="Python Developer Senior",
            company_name="TechCorp",
            job_url="https://example.com/job2",
            platform_source="indeed",
            job_description="Python developer needed",
            location="Sydney NSW",
            discovered_timestamp=datetime.now() - timedelta(days=5),
        )

        mock_jobs_repo.get_job_by_id = MagicMock(return_value=target_job)
        mock_jobs_repo.get_recent_jobs_by_title = MagicMock(return_value=[duplicate_job])
        mock_fuzzy_matcher.weighted_similarity_score = MagicMock(return_value=0.95)

        result = detector.find_duplicates("job-1")

        assert len(result["duplicates"]) == 1
        assert result["duplicates"][0]["job_id"] == "job-2"
        assert result["duplicates"][0]["similarity_score"] == 0.95
        assert result["duplicates"][0]["classification"] == "duplicate"
        assert len(result["analyze"]) == 0

    def test_find_duplicates_with_analyze_tier(self, detector, mock_jobs_repo, mock_fuzzy_matcher):
        """Test finding duplicates with Tier 2 analyze candidates."""
        target_job = Job(job_id="job-1", job_title="Senior Python Developer", company_name="TechCorp", job_url="https://example.com/job1", platform_source="seek", job_description="Python developer needed", location="Sydney, NSW")

        analyze_job = Job(
            job_id="job-3",
            job_title="Python Software Engineer",
            company_name="TechCorp",
            job_url="https://example.com/job3",
            platform_source="linkedin",
            job_description="Software engineer position",
            location="Sydney, NSW",
            discovered_timestamp=datetime.now() - timedelta(days=10),
        )

        mock_jobs_repo.get_job_by_id = MagicMock(return_value=target_job)
        mock_jobs_repo.get_recent_jobs_by_title = MagicMock(return_value=[analyze_job])
        mock_fuzzy_matcher.weighted_similarity_score = MagicMock(return_value=0.82)

        result = detector.find_duplicates("job-1")

        assert len(result["duplicates"]) == 0
        assert len(result["analyze"]) == 1
        assert result["analyze"][0]["job_id"] == "job-3"
        assert result["analyze"][0]["similarity_score"] == 0.82
        assert result["analyze"][0]["classification"] == "analyze"

    def test_find_duplicates_mixed_results(self, detector, mock_jobs_repo, mock_fuzzy_matcher):
        """Test finding duplicates with mixed results (duplicates, analyze, different)."""
        target_job = Job(job_id="job-1", job_title="Senior Python Developer", company_name="TechCorp", job_url="https://example.com/job1", platform_source="seek", job_description="Python developer needed", location="Sydney, NSW")

        candidates = [
            Job(
                job_id="job-2",
                job_title="Python Developer Senior",
                company_name="TechCorp",
                job_url="https://example.com/job2",
                platform_source="indeed",
                job_description="Python developer needed",
                location="Sydney NSW",
                discovered_timestamp=datetime.now() - timedelta(days=5),
            ),
            Job(
                job_id="job-3",
                job_title="Python Engineer",
                company_name="TechCorp",
                job_url="https://example.com/job3",
                platform_source="linkedin",
                job_description="Engineer position",
                location="Sydney, NSW",
                discovered_timestamp=datetime.now() - timedelta(days=10),
            ),
            Job(
                job_id="job-4",
                job_title="Marketing Manager",
                company_name="RetailCo",
                job_url="https://example.com/job4",
                platform_source="seek",
                job_description="Marketing role",
                location="Melbourne, VIC",
                discovered_timestamp=datetime.now() - timedelta(days=3),
            ),
        ]

        mock_jobs_repo.get_job_by_id = MagicMock(return_value=target_job)
        mock_jobs_repo.get_recent_jobs_by_title = MagicMock(return_value=candidates)

        # Mock different similarity scores for each candidate
        similarity_scores = [0.95, 0.82, 0.30]
        mock_fuzzy_matcher.weighted_similarity_score = MagicMock(side_effect=similarity_scores)

        result = detector.find_duplicates("job-1")

        assert len(result["duplicates"]) == 1  # job-2 with 0.95
        assert len(result["analyze"]) == 1  # job-3 with 0.82
        # job-4 with 0.30 is not included

    def test_find_duplicates_job_not_found(self, detector, mock_jobs_repo):
        """Test finding duplicates when target job doesn't exist."""
        mock_jobs_repo.get_job_by_id = MagicMock(return_value=None)

        with pytest.raises(ValueError, match="Job not found"):
            detector.find_duplicates("nonexistent-job")

    def test_find_duplicates_logs_decisions(self, detector, mock_jobs_repo, mock_fuzzy_matcher):
        """Test that duplicate detection logs all classification decisions."""
        target_job = Job(job_id="job-1", job_title="Senior Python Developer", company_name="TechCorp", job_url="https://example.com/job1", platform_source="seek", job_description="Python developer needed", location="Sydney, NSW")

        duplicate_job = Job(
            job_id="job-2",
            job_title="Python Developer Senior",
            company_name="TechCorp",
            job_url="https://example.com/job2",
            platform_source="indeed",
            job_description="Python developer needed",
            location="Sydney NSW",
            discovered_timestamp=datetime.now() - timedelta(days=5),
        )

        mock_jobs_repo.get_job_by_id = MagicMock(return_value=target_job)
        mock_jobs_repo.get_recent_jobs_by_title = MagicMock(return_value=[duplicate_job])
        mock_fuzzy_matcher.weighted_similarity_score = MagicMock(return_value=0.95)

        with patch("app.services.duplicate_detector.logger") as mock_logger:
            detector.find_duplicates("job-1")

            # Verify logging occurred
            assert mock_logger.info.called or mock_logger.debug.called

    def test_custom_thresholds(self):
        """Test detector with custom thresholds."""
        with patch("app.services.duplicate_detector.JobsRepository"):
            with patch("app.services.duplicate_detector.FuzzyMatcher"):
                detector = DuplicateDetector(duplicate_threshold=0.85, analyze_threshold=0.70, days_lookback=60)

                assert detector.duplicate_threshold == 0.85
                assert detector.analyze_threshold == 0.70
                assert detector.days_lookback == 60

                # Test classification with custom thresholds
                assert detector._classify_similarity(0.86) == DuplicateClassification.DUPLICATE
                assert detector._classify_similarity(0.75) == DuplicateClassification.ANALYZE
                assert detector._classify_similarity(0.69) == DuplicateClassification.DIFFERENT
