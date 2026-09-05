from openai import AsyncOpenAI

from app.core.config import settings
from app.services.voice.asr_provider import BaseASRProvider
from app.services.voice.schemas import VoiceLanguage


class QwenASRProvider(BaseASRProvider):
    name = "qwen"

    def __init__(self):
        if not settings.QWEN_API_KEY:
            raise RuntimeError("Qwen ASR is not configured.")
        if not settings.QWEN_ASR_MODEL:
            raise RuntimeError("QWEN_ASR_MODEL is not configured.")
        self._client = AsyncOpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            timeout=60.0,
        )

    async def transcribe(
        self,
        *,
        audio: bytes,
        filename: str,
        content_type: str,
        language_hint: VoiceLanguage,
        browser_transcript: str | None = None,
    ) -> str:
        kwargs = {
            "model": settings.QWEN_ASR_MODEL,
            "file": (filename or "voice.webm", audio, content_type),
        }
        if language_hint != "auto":
            kwargs["language"] = language_hint
        response = await self._client.audio.transcriptions.create(**kwargs)
        transcript = (getattr(response, "text", "") or "").strip()
        if not transcript:
            raise RuntimeError("Qwen ASR returned an empty transcript.")
        return transcript
