from app.services.voice.asr_provider import BaseASRProvider
from app.services.voice.schemas import VoiceLanguage


class MockASRProvider(BaseASRProvider):
    name = "mock"

    async def transcribe(
        self,
        *,
        audio: bytes,
        filename: str,
        content_type: str,
        language_hint: VoiceLanguage,
        browser_transcript: str | None = None,
    ) -> str:
        transcript = (browser_transcript or "").strip()
        if not transcript:
            raise ValueError(
                "Browser speech recognition did not return a transcript. "
                "Use a supported browser or configure Qwen ASR."
            )
        return transcript
