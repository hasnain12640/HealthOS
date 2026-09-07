import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_profile
from app.core.config import settings
from app.core.database import get_db
from app.models.models import HealthProfile
from app.services.ai.health_context import build_health_system_prompt
from app.services.ai.mock_provider import MockProvider
from app.services.ai.provider_factory import get_provider

logger = logging.getLogger("healthos.chat")

router = APIRouter()


class ChatHistoryItem(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatHistoryItem] = []


class ChatResponse(BaseModel):
    reply: str
    provider: str
    model: str | None = None


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    profile: HealthProfile = Depends(get_current_profile),
    db: Session = Depends(get_db),
):
    system_prompt = build_health_system_prompt(profile, db)
    history = [{"role": h.role, "content": h.content} for h in body.history[-6:]]
    history.append({"role": "user", "content": body.message})

    provider_name = settings.AI_PROVIDER
    try:
        reply = await get_provider().chat(messages=history, system_prompt=system_prompt)
    except Exception as exc:
        if settings.AI_PROVIDER == "qwen":
            logger.warning("Qwen chat failed (%s). Serving MockProvider fallback reply.", exc)
            try:
                reply = await MockProvider().chat(messages=history, system_prompt=system_prompt)
                provider_name = "mock"
            except Exception:
                raise HTTPException(
                    status_code=503,
                    detail="AI service temporarily unavailable. Please try again.",
                )
        else:
            raise HTTPException(
                status_code=503,
                detail="AI service temporarily unavailable. Please try again.",
            )

    return ChatResponse(
        reply=reply,
        provider=provider_name,
        model=settings.QWEN_MODEL if provider_name == "qwen" else None,
    )
