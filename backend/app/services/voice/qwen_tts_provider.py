import inspect

from openai import AsyncOpenAI

from app.core.config import settings
from app.services.voice.schemas import DetectedLanguage
from app.services.voice.tts_provider import BaseTTSProvider, SpeechSynthesisResult


class QwenTTSProvider(BaseTTSProvider):
    name = "qwen"

    def __init__(self):
        if not settings.QWEN_API_KEY:
            raise RuntimeError("Qwen TTS is not configured.")
        if not settings.QWEN_TTS_MODEL:
            raise RuntimeError("QWEN_TTS_MODEL is not configured.")
        if not settings.QWEN_VOICE:
            raise RuntimeError("QWEN_VOICE is not configured.")
        self._client = AsyncOpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            timeout=60.0,
        )

    async def synthesize(self, text: str, language: DetectedLanguage) -> SpeechSynthesisResult:
        response = await self._client.audio.speech.create(
            model=settings.QWEN_TTS_MODEL,
            voice=settings.QWEN_VOICE,
            input=text,
            response_format="mp3",
        )
        reader = getattr(response, "aread", None) or getattr(response, "read", None)
        if reader is None:
            raise RuntimeError("Qwen TTS returned an unreadable audio response.")
        audio = reader()
        if inspect.isawaitable(audio):
            audio = await audio
        if not audio:
            raise RuntimeError("Qwen TTS returned empty audio.")
        return SpeechSynthesisResult(audio=audio, media_type="audio/mpeg", provider=self.name)
