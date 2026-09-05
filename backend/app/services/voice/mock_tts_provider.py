from app.services.voice.schemas import DetectedLanguage
from app.services.voice.tts_provider import BaseTTSProvider, SpeechSynthesisResult


class MockTTSProvider(BaseTTSProvider):
    name = "mock"

    async def synthesize(self, text: str, language: DetectedLanguage) -> SpeechSynthesisResult:
        return SpeechSynthesisResult(audio=None, media_type=None, provider=self.name)
