from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_profile
from app.core.config import settings
from app.core.database import get_db
from app.models.models import HealthProfile
from app.services.voice.schemas import (
    SpeakFallbackResponse,
    SpeakRequest,
    TranscriptionResponse,
    VoiceCommandResponse,
    VoiceLanguage,
)
from app.services.voice.voice_service import (
    command_from_transcript,
    confirm_command,
    synthesize_speech,
    transcribe_audio,
)

router = APIRouter()

_ALLOWED_AUDIO_TYPES = {
    "audio/aac",
    "audio/m4a",
    "audio/mpeg",
    "audio/mp4",
    "audio/ogg",
    "audio/wav",
    "audio/webm",
    "audio/x-m4a",
    "audio/x-wav",
    "video/webm",
}


async def _read_audio(audio: UploadFile) -> tuple[bytes, str, str]:
    content_type = (audio.content_type or "").split(";", 1)[0].strip().lower()
    if content_type not in _ALLOWED_AUDIO_TYPES:
        raise HTTPException(status_code=415, detail="Unsupported audio format.")

    try:
        data = await audio.read(settings.VOICE_MAX_UPLOAD_BYTES + 1)
    finally:
        await audio.close()

    if not data:
        raise HTTPException(status_code=422, detail="Audio recording is empty.")
    if len(data) > settings.VOICE_MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Audio recording is too large.")
    return data, Path(audio.filename or "voice.webm").name, content_type


def _validated_browser_transcript(value: str | None) -> str | None:
    if value is None:
        return None
    transcript = value.strip()
    if len(transcript) > settings.VOICE_MAX_TRANSCRIPT_CHARS:
        raise HTTPException(status_code=422, detail="Browser transcript is too long.")
    return transcript or None


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    audio: UploadFile = File(...),
    language_hint: VoiceLanguage = Form("auto"),
    browser_transcript: str | None = Form(None),
    profile: HealthProfile = Depends(get_current_profile),
):
    del profile
    data, filename, content_type = await _read_audio(audio)
    try:
        result = await transcribe_audio(
            audio=data,
            filename=filename,
            content_type=content_type,
            language_hint=language_hint,
            browser_transcript=_validated_browser_transcript(browser_transcript),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Voice transcription is temporarily unavailable.") from exc
    return result


@router.post("/command", response_model=VoiceCommandResponse)
async def command(
    audio: UploadFile | None = File(None),
    language_hint: VoiceLanguage = Form("auto"),
    browser_transcript: str | None = Form(None),
    confirmation_token: str | None = Form(None),
    confirm: bool = Form(False),
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    if confirmation_token:
        if not confirm:
            raise HTTPException(status_code=422, detail="Confirmation is required for this command.")
        if audio is not None:
            raise HTTPException(status_code=422, detail="Send either a recording or a confirmation, not both.")
        return confirm_command(
            confirmation_token=confirmation_token,
            profile=profile,
            db=db,
        )

    if audio is None:
        raise HTTPException(status_code=422, detail="An audio recording is required.")

    data, filename, content_type = await _read_audio(audio)
    try:
        transcription = await transcribe_audio(
            audio=data,
            filename=filename,
            content_type=content_type,
            language_hint=language_hint,
            browser_transcript=_validated_browser_transcript(browser_transcript),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Voice transcription is temporarily unavailable.") from exc

    return await command_from_transcript(
        transcription=transcription,
        language_hint=language_hint,
        profile=profile,
        db=db,
    )


@router.post("/speak", response_model=None)
async def speak(
    body: SpeakRequest,
    profile: HealthProfile = Depends(get_current_profile),
):
    del profile
    speech = await synthesize_speech(body.text, body.language)
    if speech.audio and speech.media_type:
        return Response(
            content=speech.audio,
            media_type=speech.media_type,
            headers={"X-Voice-Provider": speech.provider},
        )
    return SpeakFallbackResponse(
        text=body.text,
        language=body.language,
        provider=speech.provider,
    )
