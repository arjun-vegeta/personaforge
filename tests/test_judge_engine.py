import pytest
import uuid
from unittest.mock import AsyncMock, Mock
from personaforge.backend.app.judge.evaluator import (
    JudgeEngine,
    EvaluationFailure,
    LLMFailures,
)


@pytest.fixture
def judge_engine():
    return JudgeEngine()


@pytest.mark.asyncio
async def test_judge_rule_based_looping(judge_engine):
    # Simulate a long conversation (over 30 turns)
    history = [{"role": "user", "content": "hello"}] * 31

    # We mock the LLM calls so they don't fail or take time
    judge_engine.llm.get_completion = AsyncMock(return_value="Summary text")
    judge_engine.llm.get_structured_completion = AsyncMock(
        return_value=Mock(failures=[])
    )

    result = await judge_engine.evaluate_conversation(uuid.uuid4(), history)

    assert any(f.category == "looping" for f in result.failures)
    # Status should be True because only medium severity failures exist
    assert result.pass_status is True


@pytest.mark.asyncio
async def test_judge_rule_based_latency(judge_engine):
    history = [{"role": "user", "content": "hello"}]
    metadata = {"avg_latency": 6.5}

    judge_engine.llm.get_completion = AsyncMock(return_value="Summary text")
    judge_engine.llm.get_structured_completion = AsyncMock(
        return_value=Mock(failures=[])
    )

    result = await judge_engine.evaluate_conversation(
        uuid.uuid4(), history, metadata=metadata
    )

    assert any(f.category == "latency" for f in result.failures)


@pytest.mark.asyncio
async def test_judge_llm_evaluations(judge_engine):
    history = [{"role": "agent", "content": "Hallucinated info"}]

    mock_failure = EvaluationFailure(
        category="hallucination",
        severity="high",
        reason="Agent lied",
        evidence="Turn 1: ...",
    )

    # Mock LLM response
    mock_llm_result = LLMFailures(failures=[mock_failure])
    judge_engine.llm.get_structured_completion = AsyncMock(return_value=mock_llm_result)
    judge_engine.llm.get_completion = AsyncMock(return_value="Summary")

    result = await judge_engine.evaluate_conversation(uuid.uuid4(), history)

    assert result.pass_status is False
    assert result.failures[0].category == "hallucination"
    assert result.failures[0].severity == "high"
