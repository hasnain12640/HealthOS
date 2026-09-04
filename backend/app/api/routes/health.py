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
        "database": "sqlite" if "sqlite" in settings.DATABASE_URL else "postgresql",
    }
