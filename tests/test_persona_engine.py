import pytest
from unittest.mock import AsyncMock, MagicMock
from personaforge.backend.app.personas.engine import (
    Persona,
    Identity,
    Traits,
    Goal,
    PersonaEngine,
    BehaviorActionType,
    BehaviorAction,
)


@pytest.fixture
def sample_persona():
    return Persona(
        name="Test Sarah",
        identity=Identity(name="Sarah", age=42, occupation="Teacher"),
        goals=[Goal(primary="Get a refund")],
        traits=Traits(patience=0.5, aggressiveness=0.5, trust=0.5, persistence=0.5),
    )


@pytest.mark.asyncio
async def test_emotional_state_update_helpful(sample_persona):
    engine = PersonaEngine(sample_persona)
    initial_frustration = engine.persona.emotion.frustration

    # Simulate a helpful response
    await engine.update_state(
        "I can help you with that refund.", classification="helpful"
    )

    assert engine.persona.emotion.frustration <= initial_frustration
    assert engine.persona.emotion.satisfaction > 0.5


@pytest.mark.asyncio
async def test_emotional_state_update_denied(sample_persona):
    engine = PersonaEngine(sample_persona)

    # Simulate a denial
    await engine.update_state("No refund for you.", classification="denied")

    assert engine.persona.emotion.frustration > 0.0
    assert engine.persona.emotion.satisfaction < 0.5
    assert engine.persona.memory.get("refund_denials") == 1


@pytest.mark.asyncio
async def test_stage_transition_escalate(sample_persona):
    engine = PersonaEngine(sample_persona)
    scenario_config = {"logic": {"if_refund_denied_twice": "escalate"}}

    # Simulate multiple denials to trigger ESCALATE stage
    await engine.update_state(
        "Denied 1", classification="denied", scenario_config=scenario_config
    )
    await engine.update_state(
        "Denied 2", classification="denied", scenario_config=scenario_config
    )

    assert engine.persona.current_stage == "ESCALATE"


@pytest.mark.asyncio
async def test_stage_transition_identity(sample_persona):
    engine = PersonaEngine(sample_persona)

    await engine.update_state(
        "I have verified your account.", classification="identity_verified"
    )

    assert engine.persona.current_stage == "CORE_GOAL"


@pytest.mark.asyncio
async def test_determine_action_llm_call(sample_persona):
    # Mock LLMClient
    mock_llm = MagicMock()
    mock_llm.get_structured_completion = AsyncMock()

    mock_action = BehaviorAction(
        action=BehaviorActionType.ASK_QUESTION, reason="Need more info"
    )
    mock_llm.get_structured_completion.return_value = mock_action

    engine = PersonaEngine(sample_persona, llm_client=mock_llm)
    action = await engine.determine_action([])

    assert action.action == BehaviorActionType.ASK_QUESTION
    mock_llm.get_structured_completion.assert_called_once()
