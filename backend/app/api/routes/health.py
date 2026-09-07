from fastapi import APIRouter, Request
from app.core.config import settings

router = APIRouter()


@router.get("/health")
def health_check(request: Request):
    return {
        "status": "ok",
        "service": "HealthOS API",
        "version": request.app.version,
        "ai_provider": settings.AI_PROVIDER,
        "ai_model": settings.QWEN_MODEL if settings.AI_PROVIDER == "qwen" else None,
        "database": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
    }
