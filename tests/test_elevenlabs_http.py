import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from personaforge.backend.app.integrations.elevenlabs import ElevenLabsHTTPProvider


@pytest.mark.asyncio
async def test_elevenlabs_http_provider_flow():
    provider = ElevenLabsHTTPProvider(api_key="test-api-key")

    # Mock the LLM Client to avoid actual network requests
    with patch(
        "personaforge.backend.app.integrations.elevenlabs.ElevenLabsHTTPProvider.llm"
    ) as mock_llm_prop:
        mock_llm = MagicMock()
        mock_llm.get_completion = AsyncMock(return_value="Gemini Agent response text")
        mock_llm_prop.__get__ = MagicMock(return_value=mock_llm)

        # Mock the _text_to_speech method to avoid actual HTTP requests
        provider._text_to_speech = AsyncMock(return_value=b"fake_pcm_data")

        # 1. Connect
        await provider.connect(
            agent_id="test_agent",
            policy_content="Do not say yes",
            system_prompt="Be a support agent",
            greeting="Hello support",
        )

        # Retrieve first event (greeting)
        events_iter = provider.receive_events()
        first_event = await anext(events_iter)
        assert first_event["type"] == "agent_response"
        assert first_event["agent_response"]["content"] == "Hello support"

        # 2. Send customer text
        await provider.send_text("Can I get a refund?")
        assert len(provider.history) == 3
        assert provider.history[1] == {"role": "user", "content": "Can I get a refund?"}

        # Retrieve second event (agent response)
        second_event = await anext(events_iter)
        assert second_event["type"] == "agent_response"
        assert second_event["agent_response"]["content"] == "Gemini Agent response text"

        # Verify _text_to_speech was triggered to verify TTS is working
        provider._text_to_speech.assert_called_once_with("Gemini Agent response text")

        # Cleanup
        await provider.disconnect()
