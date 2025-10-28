"""Unit tests for CoverLetterWriterAgent."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.agents.base_agent import BaseAgent
from app.agents.cover_letter_writer_agent import CoverLetterWriterAgent


class TestStructure:
    """Test agent structure."""

    def test_inherits_base_agent(self):
        config = {"model": "claude-sonnet-4"}
        agent = CoverLetterWriterAgent(config, Mock(), Mock())
        assert isinstance(agent, BaseAgent)
        assert agent.agent_name == "cover_letter_writer"

    def test_model_property(self):
        config = {"model": "claude-sonnet-4"}
        agent = CoverLetterWriterAgent(config, Mock(), Mock())
        assert agent.model == "claude-sonnet-4"


@pytest.mark.asyncio
class TestTemplateLoading:
    """Test CL template loading."""

    @patch("app.agents.cover_letter_writer_agent.Document")
    async def test_load_template_success(self, mock_doc):
        mock_doc.return_value = MagicMock()
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Create a real Path object and mock its exists() method
        test_path = Path("test.docx")
        with patch.object(Path, "exists", return_value=True):
            doc = agent._load_cl_template(test_path)
            assert doc is not None

    @patch("app.agents.cover_letter_writer_agent.Document")
    async def test_load_template_missing(self, mock_doc):
        mock_doc.side_effect = FileNotFoundError()
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        with pytest.raises(FileNotFoundError):
            agent._load_cl_template(Path("missing.docx"))


@pytest.mark.asyncio
class TestContactExtraction:
    """Test contact person extraction."""

    async def test_parse_name_from_email(self):
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        assert agent._parse_name_from_email("jane.smith@acme.com") == "Jane Smith"
        assert agent._parse_name_from_email("jsmith@acme.com") == "J Smith"

    async def test_extract_contact_person_from_email(self):
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        job_data = {"contact_email": "jane.smith@acme.com"}
        name, method = agent._extract_contact_person(job_data)
        assert name == "Jane Smith"
        assert method == "email"

    async def test_extract_contact_person_default(self):
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        job_data = {}
        name, method = agent._extract_contact_person(job_data)
        assert name == "Hiring Manager"
        assert method == "default"


@pytest.mark.asyncio
class TestCoverLetterGeneration:
    """Test CL generation with Claude."""

    async def test_generate_cover_letter_success(self):
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Dear Hiring Manager,\n\nI am writing to apply...")]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, mock_claude, Mock())
        job_context = {
            "company_name": "Acme Corp",
            "job_title": "Engineer",
            "job_description": "Test job",
            "matched_technologies": ["Python"],
        }
        contact_person = "Jane Smith"

        result = await agent._generate_cover_letter_with_claude(job_context, contact_person)
        assert "Dear Hiring Manager" in result
        assert len(result) > 40  # Adjusted for test mock response length


@pytest.mark.asyncio
class TestDOCXGeneration:
    """Test DOCX file generation."""

    @patch("app.agents.cover_letter_writer_agent.Document")
    async def test_create_cover_letter_docx(self, mock_doc):
        mock_document = MagicMock()
        mock_doc.return_value = mock_document

        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        output_path = Path("test/Linus_McManamey_CL.docx")
        cl_text = "Dear Hiring Manager,\n\nTest content"

        agent._create_cover_letter_docx(cl_text, output_path)
        mock_document.save.assert_called_once_with(output_path)


@pytest.mark.asyncio
class TestFileValidation:
    """Test output file validation."""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    @patch("app.agents.cover_letter_writer_agent.Document")
    async def test_validate_file_success(self, mock_doc, mock_stat, mock_exists):
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=50000)
        mock_doc.return_value = MagicMock()

        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        assert agent._validate_output_file(Path("test.docx")) is True

    @patch("pathlib.Path.exists")
    async def test_validate_file_missing(self, mock_exists):
        mock_exists.return_value = False
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        assert agent._validate_output_file(Path("missing.docx")) is False


@pytest.mark.asyncio
class TestProcessMethod:
    """Test main process method."""

    @patch("app.agents.cover_letter_writer_agent.Document")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    async def test_process_success(self, mock_stat, mock_exists, mock_doc):
        mock_doc.return_value = MagicMock()
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=50000)

        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text="Dear Hiring Manager,\n\nTest CL")]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(
            return_value={
                "id": "job-123",
                "title": "Engineer",
                "company_name": "Acme",
                "description": "Test",
                "contact_email": "jane@acme.com",
            }
        )
        mock_app_repo.get_stage_outputs = AsyncMock(
            return_value={
                "cv_tailor": {
                    "cv_file_path": "export_cv_cover_letter/2025-10-28_acme_engineer/Linus_McManamey_CV.docx"
                },
                "job_matcher": {"must_have_found": ["Python"]},
            }
        )

        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, mock_claude, mock_app_repo)
        result = await agent.process("job-123")

        assert result.success is True
        assert result.agent_name == "cover_letter_writer"
        assert "cl_file_path" in result.output


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error scenarios."""

    async def test_missing_job_id(self):
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        result = await agent.process(None)
        assert result.success is False
        assert "job_id" in result.error_message.lower()

    async def test_job_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_job_by_id = AsyncMock(return_value=None)
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)
        result = await agent.process("missing-job")
        assert result.success is False
        assert "not found" in result.error_message.lower()

    @patch("app.agents.cover_letter_writer_agent.Document")
    async def test_process_template_not_found(self, mock_doc):
        mock_doc.side_effect = FileNotFoundError("Template not found")
        mock_repo = AsyncMock()
        mock_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Engineer"})

        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)
        result = await agent.process("job-123")

        assert result.success is False
        assert "template not found" in result.error_message.lower()


@pytest.mark.asyncio
class TestFilenameSanitization:
    """Test filename sanitization for security."""

    async def test_sanitize_normal_text(self):
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        assert agent._sanitize_filename("Acme Corp") == "acme-corp"

    async def test_sanitize_path_traversal(self):
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        # Should remove path separators (making .. harmless)
        result = agent._sanitize_filename("../../etc/passwd")
        assert "/" not in result
        assert "\\" not in result
        # Verify result is safe (no path components)
        assert Path(f"export_cv_cover_letter/{result}").name == result

    async def test_sanitize_invalid_chars(self):
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        result = agent._sanitize_filename('Company<>:"/\\|?*Name')
        assert all(c not in result for c in '<>:"/\\|?*')

    async def test_sanitize_long_name(self):
        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        long_name = "Very Long Company Name That Exceeds Fifty Characters Limit"
        result = agent._sanitize_filename(long_name)
        assert len(result) <= 50


@pytest.mark.asyncio
class TestFileSizeValidation:
    """Test file size validation."""

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.stat")
    @patch("app.agents.cover_letter_writer_agent.Document")
    async def test_validate_file_too_large(self, mock_doc, mock_stat, mock_exists):
        mock_exists.return_value = True
        mock_stat.return_value = Mock(st_size=3 * 1024 * 1024)  # 3MB > 2MB limit
        mock_doc.return_value = MagicMock()

        agent = CoverLetterWriterAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        assert agent._validate_output_file(Path("huge.docx")) is False
