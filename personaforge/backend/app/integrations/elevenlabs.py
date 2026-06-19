import os
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
