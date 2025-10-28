"""Unit tests for QAAgent."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from app.agents.base_agent import BaseAgent
from app.agents.qa_agent import QAAgent


class TestStructure:
    """Test agent structure."""

    def test_inherits_base_agent(self):
        config = {"model": "claude-sonnet-4"}
        agent = QAAgent(config, Mock(), Mock())
        assert isinstance(agent, BaseAgent)
        assert agent.agent_name == "qa"

    def test_model_property(self):
        config = {"model": "claude-sonnet-4"}
        agent = QAAgent(config, Mock(), Mock())
        assert agent.model == "claude-sonnet-4"


@pytest.mark.asyncio
class TestDocumentLoading:
    """Test document loading from stage outputs and templates."""

    @patch("app.agents.qa_agent.Document")
    async def test_load_document_success(self, mock_doc):
        mock_doc.return_value = MagicMock()
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        with patch.object(Path, "exists", return_value=True):
            doc = agent._load_document(Path("test.docx"))
            assert doc is not None

    @patch("app.agents.qa_agent.Document")
    async def test_load_document_missing(self, mock_doc):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                agent._load_document(Path("missing.docx"))

    async def test_extract_text_from_document(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        mock_doc = MagicMock()
        mock_doc.paragraphs = [MagicMock(text="Paragraph 1"), MagicMock(text="Paragraph 2")]

        text = agent._extract_text_from_document(mock_doc)
        assert "Paragraph 1" in text
        assert "Paragraph 2" in text


@pytest.mark.asyncio
class TestAustralianEnglishChecks:
    """Test Australian English spelling checks."""

    async def test_detect_american_spelling(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        text = "I specialize in color optimization and recognize patterns."
        issues = agent._check_australian_english(text)

        assert len(issues) > 0
        assert any("color" in issue["description"].lower() for issue in issues)
        assert any("specialize" in issue["description"].lower() for issue in issues)
        assert any("recognize" in issue["description"].lower() for issue in issues)

    async def test_australian_spelling_correct(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        text = "I specialise in colour optimisation and recognise patterns."
        issues = agent._check_australian_english(text)

        # Should have no spelling issues
        spelling_issues = [i for i in issues if i["type"] == "spelling"]
        assert len(spelling_issues) == 0

    async def test_case_insensitive_spelling_check(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        text = "Color and COLOR should both be flagged."
        issues = agent._check_australian_english(text)

        assert len(issues) >= 2  # Both instances should be caught


@pytest.mark.asyncio
class TestFabricationDetection:
    """Test fabrication detection (content not in original)."""

    async def test_detect_new_skills(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        original_text = "Python, SQL, AWS"
        generated_text = "Python, SQL, AWS, Kubernetes, Docker, Terraform, Ansible, Jenkins, GitLab, Prometheus, Grafana, ELK, Kafka, RabbitMQ"

        issues = agent._check_fabrication(original_text, generated_text, "CV")

        assert len(issues) > 0
        # Should flag many new technologies as potential fabrications

    async def test_no_fabrication_when_subset(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        original_text = "Python, SQL, AWS, Kubernetes, Docker"
        generated_text = "Python, SQL, AWS"

        issues = agent._check_fabrication(original_text, generated_text, "CV")

        # Should have no fabrication issues (generated is subset of original)
        fabrication_issues = [i for i in issues if i["type"] == "fabrication"]
        assert len(fabrication_issues) == 0


@pytest.mark.asyncio
class TestContactInfoValidation:
    """Test contact information validation."""

    async def test_contact_info_matches(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        original = "Linus McManamey\nlinus@example.com\n+61 400 123 456"
        generated = "Linus McManamey\nlinus@example.com\n+61 400 123 456"

        issues = agent._check_contact_info(original, generated)

        # Should have no contact info issues
        assert len(issues) == 0

    async def test_detect_email_mismatch(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        original = "linus@example.com"
        generated = "different@example.com"

        issues = agent._check_contact_info(original, generated)

        assert len(issues) > 0
        assert any("email" in issue["description"].lower() for issue in issues)


@pytest.mark.asyncio
class TestClaudeQAAnalysis:
    """Test Claude-powered QA analysis."""

    async def test_analyze_documents_with_claude(self):
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"issues": [{"type": "spelling", "description": "American spelling detected", "severity": "critical", "location": "CV page 1"}], "recommendations": ["Good structure"]}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        agent = QAAgent({"model": "claude-sonnet-4"}, mock_claude, Mock())

        original_cv = "Original CV content"
        generated_cv = "Generated CV content with color"
        original_cl = "Original CL content"
        generated_cl = "Generated CL content"

        result = await agent._analyze_with_claude(original_cv, generated_cv, original_cl, generated_cl)

        assert "issues" in result
        assert len(result["issues"]) > 0
        assert result["issues"][0]["type"] == "spelling"


@pytest.mark.asyncio
class TestPassFailDecision:
    """Test pass/fail decision logic."""

    async def test_passes_with_no_critical_issues(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        issues = [{"type": "formatting", "description": "Minor spacing issue", "severity": "warning", "location": "CV"}]

        passed = agent._should_pass(issues)
        assert passed is True

    async def test_fails_with_critical_issues(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        issues = [{"type": "spelling", "description": "American spelling", "severity": "critical", "location": "CV"}]

        passed = agent._should_pass(issues)
        assert passed is False

    async def test_passes_with_info_issues(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        issues = [{"type": "formatting", "description": "Could bold key achievements", "severity": "info", "location": "CV"}]

        passed = agent._should_pass(issues)
        assert passed is True


@pytest.mark.asyncio
class TestProcessMethod:
    """Test main process method."""

    @patch("app.agents.qa_agent.Document")
    @patch("pathlib.Path.exists")
    async def test_process_success(self, mock_exists, mock_doc):
        mock_doc.return_value = MagicMock()
        mock_doc.return_value.paragraphs = [MagicMock(text="Test content with colour and centre")]
        mock_exists.return_value = True

        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"issues": [], "recommendations": []}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Engineer"})
        mock_app_repo.get_stage_outputs = AsyncMock(
            return_value={
                "cv_tailor": {"cv_file_path": "export_cv_cover_letter/2025-10-28_acme_engineer/Linus_McManamey_CV.docx"},
                "cover_letter_writer": {"cl_file_path": "export_cv_cover_letter/2025-10-28_acme_engineer/Linus_McManamey_CL.docx"},
            }
        )

        agent = QAAgent({"model": "claude-sonnet-4"}, mock_claude, mock_app_repo)
        result = await agent.process("job-123")

        assert result.success is True
        assert result.agent_name == "qa"
        assert "pass" in result.output
        assert result.output["pass"] is True


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error scenarios."""

    async def test_missing_job_id(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        result = await agent.process(None)
        assert result.success is False
        assert "job_id" in result.error_message.lower()

    async def test_job_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_job_by_id = AsyncMock(return_value=None)
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)
        result = await agent.process("missing-job")
        assert result.success is False
        assert "not found" in result.error_message.lower()

    async def test_missing_cv_file(self):
        mock_repo = AsyncMock()
        mock_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123"})
        mock_repo.get_stage_outputs = AsyncMock(return_value={})  # No stage outputs

        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)
        result = await agent.process("job-123")
        assert result.success is False
        assert "cv" in result.error_message.lower() or "file" in result.error_message.lower()


@pytest.mark.asyncio
class TestIssueAggregation:
    """Test aggregation of issues from multiple checks."""

    async def test_aggregate_all_issues(self):
        agent = QAAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        spelling_issues = [{"type": "spelling", "description": "color -> colour", "severity": "critical", "location": "CV"}]
        fabrication_issues = [{"type": "fabrication", "description": "New skill added", "severity": "critical", "location": "CV"}]
        contact_issues = [{"type": "contact_info", "description": "Email mismatch", "severity": "critical", "location": "CV"}]

        all_issues = agent._aggregate_issues(spelling_issues, fabrication_issues, contact_issues)

        assert len(all_issues) == 3
        assert any(i["type"] == "spelling" for i in all_issues)
        assert any(i["type"] == "fabrication" for i in all_issues)
        assert any(i["type"] == "contact_info" for i in all_issues)
