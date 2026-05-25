import os
import json
import base64
import asyncio
import websockets
from typing import AsyncIterator, Any, Optional
from .base import VoiceAgentProvider

class ElevenLabsProvider(VoiceAgentProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.agent_id: Optional[str] = None

    async def connect(self, agent_id: str, **kwargs) -> None:
        self.agent_id = agent_id
        url = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={agent_id}"
        
        headers = {}
        if self.api_key:
            headers["xi-api-key"] = self.api_key

        self.ws = await websockets.connect(url, extra_headers=headers)
        
        # Send initiation data if provided
        init_data = kwargs.get("initiation_data", {})
        if init_data:
            await self.ws.send(json.dumps({
                "type": "conversation_initiation_client_data",
                "conversation_initiation_client_data": init_data
            }))

    async def disconnect(self) -> None:
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def send_audio(self, audio_bytes: bytes) -> None:
        if not self.ws:
            raise RuntimeError("Not connected")
        
        message = {
            "type": "user_audio_chunk",
            "user_audio_chunk": base64.b64encode(audio_bytes).decode("utf-8")
        }
        await self.ws.send(json.dumps(message))

    async def send_text(self, text: str) -> None:
        if not self.ws:
            raise RuntimeError("Not connected")
        
        message = {
            "type": "user_transcript",
            "user_transcript": text
        }
        await self.ws.send(json.dumps(message))

    async def receive_events(self) -> AsyncIterator[Any]:
        if not self.ws:
            raise RuntimeError("Not connected")
        
        async for message in self.ws:
            yield json.loads(message)
