"""
Unit tests for CVTailorAgent.

Tests CV template loading, job analysis, Claude customization,
DOCX generation, and file handling.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.agents.base_agent import BaseAgent
from app.agents.cv_tailor_agent import CVTailorAgent


class TestCVTailorAgentStructure:
    """Test CVTailorAgent class structure and inheritance."""

    def test_cv_tailor_inherits_base_agent(self):
        """Verify CVTailorAgent inherits from BaseAgent."""
        config = {"model": "claude-sonnet-4"}
        claude_client = Mock()
        app_repo = Mock()

        agent = CVTailorAgent(config, claude_client, app_repo)

        assert isinstance(agent, BaseAgent)
        assert agent.agent_name == "cv_tailor"

    def test_agent_name_property(self):
        """Verify agent_name property returns correct value."""
        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        assert agent.agent_name == "cv_tailor"

    def test_model_property(self):
        """Verify model property returns claude-sonnet-4."""
        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        assert agent.model == "claude-sonnet-4"


@pytest.mark.asyncio
class TestCVTemplateLoading:
    """Test CV template loading from DOCX file."""

    @patch("app.agents.cv_tailor_agent.Document")
    async def test_load_cv_template_success(self, mock_document):
        """Test successful CV template loading."""
        mock_doc = MagicMock()
        mock_doc.paragraphs = [Mock(text="Professional Summary"), Mock(text="Work Experience")]
        mock_document.return_value = mock_doc

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        template_path = Path("current_cv_coverletter/Linus_McManamey_CV.docx")
        doc = agent._load_cv_template(template_path)

        assert doc is not None
        mock_document.assert_called_once_with(template_path)

    @patch("app.agents.cv_tailor_agent.Document")
    async def test_load_cv_template_missing_file(self, mock_document):
        """Test handling of missing CV template file."""
        mock_document.side_effect = FileNotFoundError("Template not found")

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        template_path = Path("nonexistent/template.docx")

        with pytest.raises(FileNotFoundError):
            agent._load_cv_template(template_path)

    @patch("app.agents.cv_tailor_agent.Document")
    async def test_load_cv_template_invalid_docx(self, mock_document):
        """Test handling of invalid DOCX file."""
        mock_document.side_effect = Exception("Invalid DOCX format")

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        template_path = Path("invalid.docx")

        with pytest.raises(Exception):
            agent._load_cv_template(template_path)


@pytest.mark.asyncio
class TestFilenameHandling:
    """Test filename sanitization and directory creation."""

    async def test_sanitize_filename(self):
        """Test filename sanitization."""
        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        # Test various inputs
        assert agent._sanitize_filename("Acme Corp") == "acme-corp"
        assert agent._sanitize_filename("Senior Data Engineer") == "senior-data-engineer"
        assert agent._sanitize_filename("Test/Invalid\\Chars") == "testinvalidchars"
        assert (
            agent._sanitize_filename("Very Long Company Name That Exceeds Fifty Characters Limit")
            == "very-long-company-name-that-exceeds-fifty-characte"
        )

    @patch("pathlib.Path.mkdir")
    async def test_create_output_directory(self, mock_mkdir):
        """Test output directory creation."""
        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        output_dir = agent._create_output_directory("Acme Corp", "Senior Data Engineer")

        assert "acme-corp" in str(output_dir)
        assert "senior-data-engineer" in str(output_dir)
        mock_mkdir.assert_called_once()


@pytest.mark.asyncio
class TestJobRequirementsAnalysis:
    """Test job requirements analysis and context preparation."""

    async def test_analyze_job_requirements(self):
        """Test extraction of job requirements."""
        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        job_data = {
            "title": "Senior Data Engineer",
            "company_name": "Acme Corp",
            "description": "Looking for Python and PySpark expert",
        }

        stage_outputs = {
            "job_matcher": {
                "must_have_found": ["Python", "SQL"],
                "strong_pref_found": ["PySpark", "Databricks"],
            }
        }

        context = agent._analyze_job_requirements(job_data, stage_outputs)

        assert context["job_title"] == "Senior Data Engineer"
        assert context["company_name"] == "Acme Corp"
        assert "Python" in context["matched_technologies"]
        assert "PySpark" in context["matched_technologies"]


@pytest.mark.asyncio
class TestClaudeCustomization:
    """Test Claude-based CV customization."""

    async def test_customize_cv_with_claude_success(self):
        """Test successful CV customization with Claude."""
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text=json.dumps(
                    {
                        "section_order": ["Professional Summary", "Key Skills", "Work Experience"],
                        "emphasis_skills": ["Azure", "PySpark"],
                        "keywords_to_add": ["Data Engineering", "ETL"],
                        "professional_summary": "Experienced data engineer specializing in Azure and PySpark",
                        "customization_notes": "Emphasized cloud and big data skills",
                    }
                )
            )
        ]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, mock_claude, Mock())

        cv_content = "Professional Summary\nWork Experience"
        job_context = {
            "job_title": "Senior Data Engineer",
            "company_name": "Acme Corp",
            "job_description": "Looking for data engineer with cloud experience",
            "matched_technologies": ["Azure", "PySpark"],
        }

        result = await agent._customize_cv_with_claude(cv_content, job_context)

        assert result["section_order"] == ["Professional Summary", "Key Skills", "Work Experience"]
        assert "Azure" in result["emphasis_skills"]
        assert "Data Engineering" in result["keywords_to_add"]

    async def test_customize_cv_claude_failure(self):
        """Test handling of Claude API failure."""
        mock_claude = AsyncMock()
        mock_claude.messages.create = AsyncMock(side_effect=Exception("API error"))

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, mock_claude, Mock())

        cv_content = "Professional Summary"
        job_context = {
            "job_title": "Engineer",
            "company_name": "Test Co",
            "job_description": "Test description",
            "matched_technologies": [],
        }

        with pytest.raises(Exception):
            await agent._customize_cv_with_claude(cv_content, job_context)


@pytest.mark.asyncio
class TestDOCXGeneration:
    """Test DOCX file generation and manipulation."""

    @patch("app.agents.cv_tailor_agent.Document")
    @patch("pathlib.Path.mkdir")
    async def test_generate_customized_cv(self, mock_mkdir, mock_document):
        """Test customized CV generation."""
        mock_doc = MagicMock()
        mock_doc.save = Mock()
        mock_document.return_value = mock_doc

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        customizations = {
            "section_order": ["Professional Summary", "Work Experience"],
            "emphasis_skills": ["Python"],
            "keywords_to_add": ["Data Engineering"],
            "professional_summary": "Updated summary",
            "customization_notes": "Test customization",
        }

        output_path = Path("export_cv_cover_letter/test/Linus_McManamey_CV.docx")

        agent._generate_customized_cv(mock_doc, customizations, output_path)

        mock_doc.save.assert_called_once_with(output_path)


@pytest.mark.asyncio
class TestFileValidation:
    """Test output file validation."""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    @patch("app.agents.cv_tailor_agent.Document")
    async def test_validate_output_file_success(self, mock_document, mock_stat, mock_exists):
        """Test successful file validation."""
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=1024 * 1024)  # 1MB
        mock_document.return_value = MagicMock()

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        file_path = Path("test/output.docx")
        is_valid = agent._validate_output_file(file_path)

        assert is_valid is True

    @patch("pathlib.Path.exists")
    async def test_validate_output_file_missing(self, mock_exists):
        """Test validation of missing file."""
        mock_exists.return_value = False

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        file_path = Path("nonexistent.docx")
        is_valid = agent._validate_output_file(file_path)

        assert is_valid is False

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    async def test_validate_output_file_too_large(self, mock_stat, mock_exists):
        """Test validation of oversized file."""
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=6 * 1024 * 1024)  # 6MB (over 5MB limit)

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        file_path = Path("large.docx")
        is_valid = agent._validate_output_file(file_path)

        assert is_valid is False


@pytest.mark.asyncio
class TestDatabaseUpdates:
    """Test database update operations."""

    @patch("app.agents.cv_tailor_agent.Document")
    @patch("pathlib.Path.mkdir")
    async def test_database_updates_stage_tracking(self, mock_mkdir, mock_document):
        """Test that database is updated with CV file path and stage info."""
        mock_doc = MagicMock()
        mock_doc.save = Mock()
        mock_doc.paragraphs = [Mock(text="Summary")]
        mock_document.return_value = mock_doc

        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text=json.dumps(
                    {
                        "section_order": ["Summary"],
                        "emphasis_skills": ["Python"],
                        "keywords_to_add": ["Data"],
                        "professional_summary": "Summary",
                        "customization_notes": "Test",
                    }
                )
            )
        ]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(
            return_value={
                "id": "job-123",
                "title": "Engineer",
                "company_name": "Acme",
                "description": "Test job",
            }
        )
        mock_app_repo.get_stage_outputs = AsyncMock(
            return_value={"job_matcher": {"must_have_found": ["Python"]}}
        )

        config = {"model": "claude-sonnet-4"}

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat", return_value=Mock(st_size=1024)),
        ):

            agent = CVTailorAgent(config, mock_claude, mock_app_repo)
            await agent.process("job-123")

            # Verify current stage was updated
            mock_app_repo.update_current_stage.assert_called_once_with("job-123", "cv_tailor")

            # Verify CV file path was updated
            assert (
                mock_app_repo.update_cv_file_path.called or mock_app_repo.add_completed_stage.called
            )


@pytest.mark.asyncio
class TestProcessMethod:
    """Test the main process() method."""

    @patch("app.agents.cv_tailor_agent.Document")
    @patch("pathlib.Path.mkdir")
    async def test_process_success(self, mock_mkdir, mock_document):
        """Test successful CV tailoring process."""
        mock_doc = MagicMock()
        mock_doc.save = Mock()
        mock_doc.paragraphs = [Mock(text="Summary")]
        mock_document.return_value = mock_doc

        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [
            Mock(
                text=json.dumps(
                    {
                        "section_order": ["Summary"],
                        "emphasis_skills": ["Python"],
                        "keywords_to_add": ["Data"],
                        "professional_summary": "Summary",
                        "customization_notes": "Test",
                    }
                )
            )
        ]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(
            return_value={
                "id": "job-123",
                "title": "Engineer",
                "company_name": "Acme",
                "description": "Test",
            }
        )
        mock_app_repo.get_stage_outputs = AsyncMock(
            return_value={"job_matcher": {"must_have_found": ["Python"]}}
        )

        config = {"model": "claude-sonnet-4"}

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.stat", return_value=Mock(st_size=1024)),
        ):

            agent = CVTailorAgent(config, mock_claude, mock_app_repo)
            result = await agent.process("job-123")

            assert result.success is True
            assert result.agent_name == "cv_tailor"
            assert "cv_file_path" in result.output


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling scenarios."""

    async def test_error_handling_missing_job_id(self):
        """Test handling of missing job_id."""
        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), Mock())

        result = await agent.process(None)

        assert result.success is False
        assert result.error_message is not None
        assert "job_id" in result.error_message.lower()

    async def test_error_handling_job_not_found(self):
        """Test handling when job doesn't exist."""
        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value=None)

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), mock_app_repo)

        result = await agent.process("nonexistent-job")

        assert result.success is False
        assert "not found" in result.error_message.lower()

    @patch("app.agents.cv_tailor_agent.Document")
    async def test_error_handling_missing_template(self, mock_document):
        """Test handling of missing CV template."""
        mock_document.side_effect = FileNotFoundError("Template not found")

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(
            return_value={
                "id": "job-123",
                "title": "Engineer",
                "company_name": "Acme",
                "description": "Test",
            }
        )

        config = {"model": "claude-sonnet-4"}
        agent = CVTailorAgent(config, Mock(), mock_app_repo)

        result = await agent.process("job-123")

        assert result.success is False
        assert (
            "template" in result.error_message.lower()
            or "not found" in result.error_message.lower()
        )
