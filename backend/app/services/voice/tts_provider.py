from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.services.voice.schemas import DetectedLanguage


@dataclass
class SpeechSynthesisResult:
    audio: bytes | None
    media_type: str | None
    provider: str


class BaseTTSProvider(ABC):
    name: str

    @abstractmethod
    async def synthesize(self, text: str, language: DetectedLanguage) -> SpeechSynthesisResult:
        raise NotImplementedError
