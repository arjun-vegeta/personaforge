import os
from typing import List, Dict, Optional, Type
from pydantic import BaseModel
from google import genai
from google.genai import types


class LLMClient:
    def __init__(
        self, api_key: Optional[str] = None, model: str = "gemini-3.1-flash-lite"
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model
        self._client: Optional[genai.Client] = None

    @property
    def client(self) -> genai.Client:
        if not self._client:
            if not self.api_key:
                raise ValueError("GOOGLE_API_KEY is not set. LLM calls will fail.")
            self._client = genai.Client(
                api_key=self.api_key, http_options={"api_version": "v1alpha"}
            )
        return self._client

    async def get_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        # Convert OpenAI-style messages to a single prompt for simplicity in POC
        prompt = ""
        for msg in messages:
            role = "Model" if msg["role"] == "assistant" else "User"
            if msg["role"] == "system":
                prompt += f"System: {msg['content']}\n"
            else:
                prompt += f"{role}: {msg['content']}\n"

        config = types.GenerateContentConfig(
            temperature=temperature, max_output_tokens=max_tokens
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name, contents=prompt, config=config
        )
        return response.text

    async def get_structured_completion(
        self,
        messages: List[Dict[str, str]],
        response_format: Type[BaseModel],
        temperature: float = 0.0,
    ) -> BaseModel:
        prompt = ""
        for msg in messages:
            role = "Model" if msg["role"] == "assistant" else "User"
            if msg["role"] == "system":
                prompt += f"System: {msg['content']}\n"
            else:
                prompt += f"{role}: {msg['content']}\n"

        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
            response_schema=response_format,
        )

        response = await self.client.aio.models.generate_content(
            model=self.model_name, contents=prompt, config=config
        )
        return response_format.model_validate_json(response.text)
