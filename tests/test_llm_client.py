import pytest
from pydantic import BaseModel
from unittest.mock import AsyncMock, MagicMock
from personaforge.backend.app.integrations.llm import LLMClient

class MockResponse(BaseModel):
    answer: str

@pytest.fixture
def mock_genai_client(mocker):
    mock_client = MagicMock()
    # Mock the nested aio.models.generate_content call
    mock_aio = MagicMock()
    mock_models = MagicMock()
    mock_generate = AsyncMock()
    
    mock_client.aio = mock_aio
    mock_aio.models = mock_models
    mock_models.generate_content = mock_generate
    
    mocker.patch("personaforge.backend.app.integrations.llm.genai.Client", return_value=mock_client)
    return mock_generate

@pytest.mark.asyncio
async def test_llm_get_completion(mock_genai_client):
    client = LLMClient(api_key="test-key")
    
    mock_genai_client.return_value = MagicMock(text="Gemini Response")
    
    messages = [{"role": "user", "content": "Hello"}]
    response = await client.get_completion(messages)
    
    assert response == "Gemini Response"
    mock_genai_client.assert_called_once()

@pytest.mark.asyncio
async def test_llm_get_structured_completion(mock_genai_client):
    client = LLMClient(api_key="test-key")
    
    mock_genai_client.return_value = MagicMock(text='{"answer": "Structured Response"}')
    
    messages = [{"role": "user", "content": "Query"}]
    result = await client.get_structured_completion(messages, MockResponse)
    
    assert result.answer == "Structured Response"
    assert isinstance(result, MockResponse)
