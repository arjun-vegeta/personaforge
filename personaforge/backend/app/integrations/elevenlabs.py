import os
import asyncio
import json
import base64
import websockets
import httpx
from typing import AsyncIterator, Any, Optional
from personaforge.backend.app.integrations.base import VoiceAgentProvider


class ElevenLabsProvider(VoiceAgentProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.agent_id: Optional[str] = None
        self.http_client = httpx.AsyncClient(
            headers={"xi-api-key": self.api_key} if self.api_key else {}
        )

    async def connect(self, agent_id: str, **kwargs) -> None:
        self.agent_id = agent_id
        url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"

        headers = {}
        if self.api_key:
            headers["xi-api-key"] = self.api_key

        self.ws = await websockets.connect(url, additional_headers=headers)

        # Send initiation data if provided
        init_data = kwargs.get("initiation_data", {})
        if init_data:
            await self.ws.send(
                json.dumps(
                    {
                        "type": "conversation_initiation_client_data",
                        "conversation_initiation_client_data": init_data,
                    }
                )
            )

    async def disconnect(self) -> None:
        if self.ws:
            await self.ws.close()
            self.ws = None
        await self.http_client.aclose()

    async def send_audio(self, audio_bytes: bytes) -> None:
        if not self.ws:
            raise RuntimeError("Not connected")

        # Audio must be Base64 encoded PCM (16-bit, 16kHz, Mono)
        message = {
            "type": "user_audio_chunk",
            "user_audio_chunk": base64.b64encode(audio_bytes).decode("utf-8"),
        }
        await self.ws.send(json.dumps(message))

    async def send_text(self, text: str) -> None:
        if not self.ws:
            raise RuntimeError("Not connected")

        message = {"type": "user_transcript", "user_transcript": text}
        await self.ws.send(json.dumps(message))

    async def receive_events(self) -> AsyncIterator[Any]:
        if not self.ws:
            raise RuntimeError("Not connected")

        async for message in self.ws:
            data = json.loads(message)
            # Automatic pong handling
            if data.get("type") == "ping":
                event_id = data.get("ping_event", {}).get("event_id")
                await self.ws.send(json.dumps({"type": "pong", "event_id": event_id}))
            yield data

    async def text_to_speech(
        self, text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL"
    ) -> bytes:
        """Convert text to PCM audio using ElevenLabs TTS API."""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

        # Request PCM 16kHz for compatibility with ConvAI
        params = {"output_format": "pcm_16000"}
        data = {
            "text": text,
            "model_id": "eleven_flash_v2_5",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
        }

        response = await self.http_client.post(url, json=data, params=params)
        if response.status_code != 200:
            raise Exception(f"TTS Error: {response.text}")

        return response.content


class ElevenLabsHTTPProvider(VoiceAgentProvider):
    """Voice agent provider that uses Gemini LLM locally for agent intelligence
    and ElevenLabs HTTP POST Text-to-Speech API for voice generation,
    completely bypassing the ElevenLabs WebSocket/ConvAI tier.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.http_client = httpx.AsyncClient(
            headers={"xi-api-key": self.api_key} if self.api_key else {}
        )
        self.history = []
        self.event_queue = asyncio.Queue()
        self.policy_content = ""
        self.system_prompt = ""
        self._llm = None

    @property
    def llm(self):
        if not self._llm:
            from personaforge.backend.app.integrations.llm import LLMClient

            self._llm = LLMClient()
        return self._llm

    async def connect(self, agent_id: str, **kwargs) -> None:
        self.agent_id = agent_id
        self.policy_content = kwargs.get("policy_content", "")
        self.system_prompt = kwargs.get(
            "system_prompt", "You are a helpful customer support agent."
        )

        # Enqueue the initial greeting turn
        greeting = kwargs.get(
            "greeting", "Hello, thank you for calling. How can I help you today?"
        )
        self.history.append({"role": "assistant", "content": greeting})

        await self.event_queue.put(
            {
                "type": "agent_response",
                "agent_response": {"content": greeting},
            }
        )

    async def disconnect(self) -> None:
        await self.http_client.aclose()

    async def send_audio(self, audio_bytes: bytes) -> None:
        # Since we are not streaming audio to a live WebSocket STT, we rely on send_text fallback.
        pass

    async def send_text(self, text: str) -> None:
        self.history.append({"role": "user", "content": text})

        # Build prompt messages for local Gemini agent
        messages = [
            {
                "role": "system",
                "content": f"You are a professional customer support voice agent.\n"
                f"Your instructions: {self.system_prompt}\n\n"
                f"Strict Business Policy Guidelines you must follow:\n{self.policy_content}\n\n"
                f"Guidelines rules:\n"
                f"1. Keep responses short and conversational (1-3 sentences max) since this is a voice call.\n"
                f"2. Be polite and helpful, but adhere strictly to the policy rules.\n"
                f"3. Address the customer directly.",
            }
        ]
        for turn in self.history:
            role = "assistant" if turn["role"] == "assistant" else "user"
            messages.append({"role": role, "content": turn["content"]})

        agent_reply = await self.llm.get_completion(messages)
        self.history.append({"role": "assistant", "content": agent_reply})

        # Generate voice over HTTP TTS to verify voice generation works and save to artifacts
        if self.api_key:
            try:
                await self._text_to_speech(agent_reply)
            except Exception as e:
                # Log warning, don't block conversation flow
                print(f"  (HTTP TTS Generation warning: {e})")

        await self.event_queue.put(
            {
                "type": "agent_response",
                "agent_response": {"content": agent_reply},
            }
        )

    async def receive_events(self) -> AsyncIterator[Any]:
        # Yield the events generated by connect/send_text
        while True:
            event = await self.event_queue.get()
            yield event
            self.event_queue.task_done()

    async def _text_to_speech(
        self, text: str, voice_id: str = "EXAVITQu4vr4xnSDxMaL"
    ) -> bytes:
        """Convert text to PCM audio using ElevenLabs TTS HTTP API."""
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
        params = {"output_format": "pcm_16000"}
        data = {
            "text": text,
            "model_id": "eleven_flash_v2_5",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.8},
        }

        response = await self.http_client.post(url, json=data, params=params)
        if response.status_code != 200:
            raise Exception(f"TTS Error: {response.text}")

        # Save last generated turn audio to artifacts
        os.makedirs("artifacts", exist_ok=True)
        with open("artifacts/http_agent_turn.pcm", "wb") as f:
            f.write(response.content)

        return response.content
