import pytest
import uuid
import json
import os
import yaml
from unittest.mock import MagicMock, patch, AsyncMock
from personaforge.backend.app.runner.workers import (
    _run_conversation_internal,
    _run_evaluation_internal,
    run_report_task,
)
from personaforge.backend.app.personas.engine import BehaviorAction, BehaviorActionType


@pytest.mark.asyncio
async def test_run_conversation_task_dry_run(tmp_path):
    # Setup mock environment
    os.chdir(tmp_path)
    os.makedirs("personas", exist_ok=True)
    persona_data = {
        "name": "test_customer",
        "identity": {"name": "Test", "language": "English"},
        "goals": [{"primary": "test"}],
        "traits": {},
        "behaviors": {},
        "termination": {"max_turns": 5},
    }
    with open("personas/test_customer.yaml", "w") as f:
        yaml.dump(persona_data, f)

    scenario_config = {"name": "test_scenario", "steps": []}

    # We need to mock LLMClient to avoid API calls during PersonaEngine init/run
    with patch("personaforge.backend.app.personas.engine.LLMClient") as mock_llm_class:
        mock_llm = mock_llm_class.return_value
        # get_structured_completion and get_completion must be awaitable
        mock_llm.get_structured_completion = AsyncMock(
            return_value=BehaviorAction(action=BehaviorActionType.SPEAK, reason="test")
        )
        mock_llm.get_completion = AsyncMock(return_value="Mock response")

        result = await _run_conversation_internal(
            scenario_config, "test_customer", "mock_agent", dry_run=True
        )

        assert result["persona"] == "test_customer"
        assert "history" in result
        assert os.path.exists(
            f"artifacts/conversations/{result['conversation_id']}.json"
        )


@pytest.mark.asyncio
async def test_run_evaluation_task():
    history = [{"role": "user", "content": "hello"}]
    scenario_config = {"name": "test"}

    with patch("personaforge.backend.app.judge.evaluator.LLMClient") as mock_llm_class:
        mock_llm = mock_llm_class.return_value
        mock_llm.get_structured_completion = AsyncMock(
            return_value=MagicMock(failures=[])
        )
        mock_llm.get_completion = AsyncMock(return_value="Summary")

        conv_id = str(uuid.uuid4())
        result = await _run_evaluation_internal(
            conv_id, history, "Policy", scenario_config
        )

        assert result["pass_status"] is True
        assert os.path.exists(f"artifacts/evaluations/{conv_id}.json")


def test_run_report_task(tmp_path):
    os.chdir(tmp_path)
    run_results = [
        {
            "conversation_id": "1",
            "history": [{"role": "agent", "content": "hello" * 100}],  # 500 chars
            "evaluation": {"pass_status": True, "failures": []},
        }
    ]

    report_path = run_report_task(run_results, "test_report")
    assert os.path.exists(report_path)

    with open(report_path, "r") as f:
        data = json.load(f)
        assert data["report_id"] == "test_report"
        # 500 chars TTS = 0.5 * 0.30 = 0.15. + 0.001 LLM = 0.151
        assert data["total_cost"] == pytest.approx(0.151)
