import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect
from app.core.config import settings
from app.core.database import create_tables, SessionLocal, engine
from app.api.deps import get_current_user
from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.profile import router as profile_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.lab_reports import router as lab_router
from app.api.routes.lifestyle import router as lifestyle_router
from app.api.routes.analysis import router as analysis_router
from app.api.routes.chat import router as chat_router
from app.api.routes.plan import router as plan_router
from app.api.routes.insights import router as insights_router
from app.api.routes.wearables import router as wearables_router
from app.api.routes.cycles import router as cycles_router
from app.api.routes.voice import router as voice_router
from app.api.routes.history import router as history_router
from app.services.seed import seed_demo_data

logging.basicConfig(level=logging.INFO)


def _check_schema():
    """Verify the database schema is up to date before seeding/running."""
    inspector = inspect(engine)
    if "health_profiles" in inspector.get_table_names():
        columns = {c["name"] for c in inspector.get_columns("health_profiles")}
        if "user_id" not in columns:
            raise RuntimeError(
                "Database schema is out of date (health_profiles.user_id is missing). "
                "Stop the backend, rename backend/healthos.db to backend/healthos.db.backup, and restart."
            )


app = FastAPI(
    title="HealthOS API",
    description="HealthOS — Your Personal Health Intelligence Layer",
    version="0.8.0-milestone8",
)

origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]

if settings.ENVIRONMENT == "production" and "*" in origins:
    raise RuntimeError("Wildcard CORS origin is not allowed in production.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.on_event("startup")
def startup():
    if not settings.SECRET_KEY:
        raise RuntimeError(
            "SECRET_KEY is not set. Copy backend/.env.example to backend/.env and set a secure SECRET_KEY."
        )
    create_tables()
    _check_schema()
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()


# Public routers
app.include_router(health_router, prefix="/api/v1", tags=["Health Check"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

# Protected routers
protected_dependencies = [Depends(get_current_user)]
app.include_router(profile_router,   prefix="/api/v1/profile",   tags=["Profile"],          dependencies=protected_dependencies)
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"],        dependencies=protected_dependencies)
app.include_router(lab_router,       prefix="/api/v1/lab",       tags=["Lab Reports"],      dependencies=protected_dependencies)
app.include_router(lifestyle_router, prefix="/api/v1/lifestyle", tags=["Lifestyle Logs"],    dependencies=protected_dependencies)
app.include_router(analysis_router,  prefix="/api/v1/analysis",  tags=["Health Analysis"],  dependencies=protected_dependencies)
app.include_router(chat_router,      prefix="/api/v1/chat",      tags=["AI Chat"],          dependencies=protected_dependencies)
app.include_router(plan_router,      prefix="/api/v1/plan",      tags=["AI 7-Day Plan"],    dependencies=protected_dependencies)
app.include_router(insights_router,  prefix="/api/v1/insights",  tags=["AI Insights"],      dependencies=protected_dependencies)
app.include_router(wearables_router, prefix="/api/v1/wearables", tags=["Wearables"],        dependencies=protected_dependencies)
app.include_router(cycles_router,   prefix="/api/v1",         tags=["Women's Health"],    dependencies=protected_dependencies)
app.include_router(voice_router,    prefix="/api/v1/voice",   tags=["Voice Agent"],       dependencies=protected_dependencies)
app.include_router(history_router,  prefix="/api/v1/history", tags=["History"],            dependencies=protected_dependencies)


@app.get("/")
def root():
    return {"message": "HealthOS API is running", "docs": "/docs"}
