from abc import ABC, abstractmethod
from typing import AsyncIterator, Any

class VoiceAgentProvider(ABC):
    @abstractmethod
    async def connect(self, agent_id: str, **kwargs) -> None:
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        pass

    @abstractmethod
    async def send_audio(self, audio_bytes: bytes) -> None:
        pass

    @abstractmethod
    async def send_text(self, text: str) -> None:
        pass

    @abstractmethod
    async def receive_events(self) -> AsyncIterator[Any]:
        pass
