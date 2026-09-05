from abc import ABC, abstractmethod

from app.services.voice.schemas import VoiceLanguage


class BaseASRProvider(ABC):
    name: str

    @abstractmethod
    async def transcribe(
        self,
        *,
        audio: bytes,
        filename: str,
        content_type: str,
        language_hint: VoiceLanguage,
        browser_transcript: str | None = None,
    ) -> str:
        raise NotImplementedError
