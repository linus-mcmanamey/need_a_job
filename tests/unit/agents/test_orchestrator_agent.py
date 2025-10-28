"""Unit tests for OrchestratorAgent."""

from unittest.mock import AsyncMock, Mock

import pytest

from app.agents.base_agent import BaseAgent
from app.agents.orchestrator_agent import OrchestratorAgent


class TestStructure:
    """Test agent structure."""

    def test_inherits_base_agent(self):
        config = {"model": "claude-sonnet-4"}
        agent = OrchestratorAgent(config, Mock(), Mock())
        assert isinstance(agent, BaseAgent)
        assert agent.agent_name == "orchestrator"

    def test_model_property(self):
        config = {"model": "claude-sonnet-4"}
        agent = OrchestratorAgent(config, Mock(), Mock())
        assert agent.model == "claude-sonnet-4"


@pytest.mark.asyncio
class TestStageVerification:
    """Test verification of previous pipeline stages."""

    async def test_verify_all_stages_completed(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        stage_outputs = {
            "job_matcher": {"match_score": 85.5, "reasoning": "Good match"},
            "salary_validator": {"passed": True, "analysis": "Within range"},
            "cv_tailor": {"cv_file_path": "path/to/cv.docx"},
            "cover_letter_writer": {"cl_file_path": "path/to/cl.docx"},
            "qa": {"pass": True, "issues": []},
        }

        result = agent._verify_required_stages(stage_outputs)
        assert result is True

    async def test_verify_missing_stage(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Missing qa stage
        stage_outputs = {"job_matcher": {"match_score": 85.5}, "salary_validator": {"passed": True}, "cv_tailor": {"cv_file_path": "path/to/cv.docx"}, "cover_letter_writer": {"cl_file_path": "path/to/cl.docx"}}

        result = agent._verify_required_stages(stage_outputs)
        assert result is False

    async def test_extract_metrics_from_stages(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        stage_outputs = {"job_matcher": {"match_score": 87.5, "reasoning": "Good match"}, "salary_validator": {"passed": True, "analysis": "Within range"}, "qa": {"pass": True, "issues": []}}

        metrics = agent._extract_metrics(stage_outputs)
        assert metrics["match_score"] == 87.5
        assert metrics["salary_passed"] is True
        assert metrics["qa_passed"] is True


@pytest.mark.asyncio
class TestAutoApproveDecision:
    """Test auto-approve decision path."""

    async def test_auto_approve_criteria(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        metrics = {
            "match_score": 90.0,  # >= 85
            "salary_passed": True,
            "qa_passed": True,
        }

        decision = agent._apply_decision_rules(metrics)
        assert decision == "auto_approve"

    async def test_auto_approve_edge_case(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Exactly 85% match
        metrics = {
            "match_score": 85.0,  # exactly 85
            "salary_passed": True,
            "qa_passed": True,
        }

        decision = agent._apply_decision_rules(metrics)
        assert decision == "auto_approve"


@pytest.mark.asyncio
class TestNeedsApprovalDecision:
    """Test needs human approval decision path."""

    async def test_needs_approval_medium_match(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Medium match score (60-84%)
        metrics = {
            "match_score": 75.0,  # 60-84 range
            "salary_passed": True,
            "qa_passed": True,
        }

        decision = agent._apply_decision_rules(metrics)
        assert decision == "needs_human_approval"

    async def test_needs_approval_salary_warning(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # High match but salary has warnings
        metrics = {
            "match_score": 90.0,
            "salary_passed": True,
            "salary_has_warnings": True,  # flag for warnings
            "qa_passed": True,
        }

        decision = agent._apply_decision_rules(metrics)
        # With warnings, should need human approval
        assert decision == "needs_human_approval"

    async def test_needs_approval_qa_warnings(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # QA passed but has warnings
        metrics = {
            "match_score": 90.0,
            "salary_passed": True,
            "qa_passed": True,
            "qa_has_warnings": True,  # flag for warnings
        }

        decision = agent._apply_decision_rules(metrics)
        assert decision == "needs_human_approval"


@pytest.mark.asyncio
class TestAutoRejectDecision:
    """Test auto-reject decision path."""

    async def test_auto_reject_low_match(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Low match score (< 60%)
        metrics = {
            "match_score": 50.0,  # < 60
            "salary_passed": True,
            "qa_passed": True,
        }

        decision = agent._apply_decision_rules(metrics)
        assert decision == "auto_reject"

    async def test_auto_reject_salary_failed(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # Salary validation failed
        metrics = {
            "match_score": 90.0,
            "salary_passed": False,  # failed
            "qa_passed": True,
        }

        decision = agent._apply_decision_rules(metrics)
        assert decision == "auto_reject"

    async def test_auto_reject_qa_failed(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        # QA failed
        metrics = {
            "match_score": 90.0,
            "salary_passed": True,
            "qa_passed": False,  # failed
        }

        decision = agent._apply_decision_rules(metrics)
        assert decision == "auto_reject"


@pytest.mark.asyncio
class TestClaudeDecisionSupport:
    """Test Claude-powered decision support."""

    async def test_get_claude_recommendation(self):
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"recommended_decision": "auto_approve", "reasoning": "Strong match with no concerns", "confidence": 0.92, "flagged_concerns": []}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, mock_claude, Mock())

        job_data = {"title": "Senior Data Engineer", "company": "Acme Corp"}
        stage_outputs = {"job_matcher": {"match_score": 90.0, "reasoning": "Excellent match"}, "salary_validator": {"passed": True, "analysis": "Within range"}, "qa": {"pass": True, "issues": []}}

        result = await agent._get_claude_recommendation(job_data, stage_outputs)

        assert "recommended_decision" in result
        assert result["recommended_decision"] == "auto_approve"
        assert result["confidence"] == 0.92

    async def test_claude_api_failure_fallback(self):
        mock_claude = AsyncMock()
        mock_claude.messages.create = AsyncMock(side_effect=Exception("API error"))

        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, mock_claude, Mock())

        job_data = {"title": "Senior Data Engineer"}
        stage_outputs = {"job_matcher": {"match_score": 90.0}, "salary_validator": {"passed": True}, "qa": {"pass": True}}

        # Should return safe fallback
        result = await agent._get_claude_recommendation(job_data, stage_outputs)

        assert "recommended_decision" in result
        assert result["recommended_decision"] == "needs_human_approval"  # safe default


@pytest.mark.asyncio
class TestDecisionCombination:
    """Test combining rule-based and Claude decisions."""

    async def test_combine_matching_decisions(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        rule_decision = "auto_approve"
        claude_rec = {"recommended_decision": "auto_approve", "confidence": 0.90}

        final = agent._combine_decisions(rule_decision, claude_rec)
        # Both agree, high confidence
        assert final == "auto_approve"

    async def test_combine_conflicting_decisions(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        rule_decision = "auto_approve"
        claude_rec = {"recommended_decision": "needs_human_approval", "confidence": 0.85}

        final = agent._combine_decisions(rule_decision, claude_rec)
        # Conflict: defer to human
        assert final == "needs_human_approval"

    async def test_combine_low_confidence_claude(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        rule_decision = "auto_approve"
        claude_rec = {
            "recommended_decision": "auto_approve",
            "confidence": 0.50,  # low confidence
        }

        final = agent._combine_decisions(rule_decision, claude_rec)
        # Low confidence: defer to human
        assert final == "needs_human_approval"


@pytest.mark.asyncio
class TestDatabaseUpdates:
    """Test database update logic."""

    async def test_update_for_auto_approve(self):
        mock_repo = AsyncMock()
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)

        decision_output = {"decision": "auto_approve", "reasoning": "High match, all validations passed", "confidence": 0.90, "match_score": 90.0, "salary_passed": True, "qa_passed": True}

        await agent._update_database("job-123", decision_output)

        # Should update status to "approved"
        mock_repo.update_status.assert_called_once_with("job-123", "approved")

    async def test_update_for_needs_approval(self):
        mock_repo = AsyncMock()
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)

        decision_output = {"decision": "needs_human_approval", "reasoning": "Medium match, needs review", "confidence": 0.75}

        await agent._update_database("job-123", decision_output)

        # Should update status to "pending_approval"
        mock_repo.update_status.assert_called_once_with("job-123", "pending_approval")

    async def test_update_for_auto_reject(self):
        mock_repo = AsyncMock()
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)

        decision_output = {"decision": "auto_reject", "reasoning": "Low match score", "confidence": 0.95}

        await agent._update_database("job-123", decision_output)

        # Should update status to "rejected"
        mock_repo.update_status.assert_called_once_with("job-123", "rejected")


@pytest.mark.asyncio
class TestProcessMethod:
    """Test main process method."""

    async def test_process_auto_approve_success(self):
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"recommended_decision": "auto_approve", "reasoning": "Excellent match", "confidence": 0.95, "flagged_concerns": []}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Senior Data Engineer"})
        mock_app_repo.get_stage_outputs = AsyncMock(
            return_value={
                "job_matcher": {"match_score": 90.0, "reasoning": "Great match"},
                "salary_validator": {"passed": True, "analysis": "Within range"},
                "cv_tailor": {"cv_file_path": "path/to/cv.docx"},
                "cover_letter_writer": {"cl_file_path": "path/to/cl.docx"},
                "qa": {"pass": True, "issues": []},
            }
        )

        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, mock_claude, mock_app_repo)
        result = await agent.process("job-123")

        assert result.success is True
        assert result.agent_name == "orchestrator"
        assert "decision" in result.output
        assert result.output["decision"] == "auto_approve"

    async def test_process_needs_approval_success(self):
        mock_claude = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text='{"recommended_decision": "needs_human_approval", "reasoning": "Medium match", "confidence": 0.70, "flagged_concerns": ["salary slightly low"]}')]
        mock_claude.messages.create = AsyncMock(return_value=mock_response)

        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Data Engineer"})
        mock_app_repo.get_stage_outputs = AsyncMock(
            return_value={
                "job_matcher": {"match_score": 72.0, "reasoning": "Decent match"},
                "salary_validator": {"passed": True, "analysis": "Lower end"},
                "cv_tailor": {"cv_file_path": "path/to/cv.docx"},
                "cover_letter_writer": {"cl_file_path": "path/to/cl.docx"},
                "qa": {"pass": True, "issues": []},
            }
        )

        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, mock_claude, mock_app_repo)
        result = await agent.process("job-123")

        assert result.success is True
        assert result.output["decision"] == "needs_human_approval"


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error scenarios."""

    async def test_missing_job_id(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())
        result = await agent.process(None)
        assert result.success is False
        assert "job_id" in result.error_message.lower()

    async def test_job_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_job_by_id = AsyncMock(return_value=None)
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), mock_repo)
        result = await agent.process("missing-job")
        assert result.success is False
        assert "not found" in result.error_message.lower()

    async def test_missing_required_stages(self):
        mock_app_repo = AsyncMock()
        mock_app_repo.get_job_by_id = AsyncMock(return_value={"id": "job-123", "title": "Engineer"})
        # Missing qa stage
        mock_app_repo.get_stage_outputs = AsyncMock(return_value={"job_matcher": {"match_score": 90.0}, "salary_validator": {"passed": True}})

        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), mock_app_repo)
        result = await agent.process("job-123")
        assert result.success is False
        assert "required stages" in result.error_message.lower()


@pytest.mark.asyncio
class TestReasoningGeneration:
    """Test decision reasoning generation."""

    async def test_generate_reasoning_auto_approve(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        metrics = {"match_score": 92.0, "salary_passed": True, "qa_passed": True}
        decision = "auto_approve"

        reasoning = agent._generate_reasoning(decision, metrics)
        assert "92" in reasoning  # match score mentioned
        assert "auto" in reasoning.lower()
        assert len(reasoning) > 20  # substantial explanation

    async def test_generate_reasoning_auto_reject(self):
        agent = OrchestratorAgent({"model": "claude-sonnet-4"}, Mock(), Mock())

        metrics = {"match_score": 45.0, "salary_passed": False, "qa_passed": True}
        decision = "auto_reject"

        reasoning = agent._generate_reasoning(decision, metrics)
        assert "45" in reasoning or "low" in reasoning.lower()
        assert "reject" in reasoning.lower()
