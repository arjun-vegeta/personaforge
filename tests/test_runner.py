import pytest
import uuid
from unittest.mock import AsyncMock, Mock
from personaforge.backend.app.runner.runner import ConversationRunner
from personaforge.backend.app.personas.engine import BehaviorAction, BehaviorActionType

@pytest.fixture
def runner_deps(mocker):
    provider = Mock()
    provider.connect = AsyncMock()
    provider.disconnect = AsyncMock()
    provider.send_text = AsyncMock()
    provider.send_audio = AsyncMock()
    provider.text_to_speech = AsyncMock(return_value=b"fake_audio")
    provider.receive_events = AsyncMock()
    
    persona_engine = Mock()
    persona_engine.update_state = AsyncMock()
    persona_engine.determine_action = AsyncMock()
    persona_engine.generate_utterance = AsyncMock()
    
    # Mock persona with termination
    persona_engine.persona = Mock()
    persona_engine.persona.termination = Mock()
    persona_engine.persona.termination.max_turns = 10
    
    return provider, persona_engine

@pytest.mark.asyncio
async def test_runner_handle_agent_response(runner_deps):
    provider, persona_engine = runner_deps
    conv_id = uuid.uuid4()
    runner = ConversationRunner(conv_id, "agent-123", provider, persona_engine)
    
    # Mock behavior action
    persona_engine.determine_action.return_value = BehaviorAction(
        action=BehaviorActionType.SPEAK, 
        reason="Continuing"
    )
    persona_engine.generate_utterance.return_value = "Hello back"
    
    event = {
        "type": "agent_response",
        "agent_response": {"content": "Hi there"}
    }
    
    await runner.handle_event(event)
    
    # Check interactions
    assert persona_engine.update_state.called
    assert persona_engine.determine_action.called
    assert persona_engine.generate_utterance.called
    assert provider.send_audio.called
    assert len(runner.history) == 2 # agent + customer

@pytest.mark.asyncio
async def test_runner_handle_end_call(runner_deps):
    provider, persona_engine = runner_deps
    conv_id = uuid.uuid4()
    runner = ConversationRunner(conv_id, "agent-123", provider, persona_engine)
    runner.is_running = True
    
    persona_engine.determine_action.return_value = BehaviorAction(
        action=BehaviorActionType.END_CALL, 
        reason="Goal met"
    )
    
    event = {
        "type": "agent_response",
        "agent_response": {"content": "Goodbye"}
    }
    
    await runner.handle_event(event)
    
    assert runner.is_running is False
    assert not persona_engine.generate_utterance.called
