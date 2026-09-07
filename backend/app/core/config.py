from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite:///./healthos.db"
    AI_PROVIDER: str = "mock"
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-plus"
    QWEN_BASE_URL: str = "https://ws-yvjlsrp250nie9ue.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"

    # Voice Agent (an empty provider follows AI_PROVIDER)
    VOICE_PROVIDER: str = ""
    QWEN_ASR_MODEL: str = "qwen-audio-asr"
    QWEN_TTS_MODEL: str = "qwen-tts"
    QWEN_VOICE: str = "Cherry"
    VOICE_LANGUAGE: str = "auto"
    VOICE_MAX_UPLOAD_BYTES: int = 10_000_000
    VOICE_MAX_TRANSCRIPT_CHARS: int = 3000
    VOICE_CONFIRMATION_TTL_SECONDS: int = 300

    # Authentication
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Demo account (optional; seeding skipped if DEMO_PASSWORD is empty)
    DEMO_EMAIL: str = "demo@healthos.pk"
    DEMO_PASSWORD: str = ""
    SEED_DEMO_DATA: bool = True

    # Female demo account (Women's Health showcase; uses the same DEMO_PASSWORD)
    FEMALE_DEMO_EMAIL: str = "ayesha@healthos.pk"

    # CORS (comma-separated origins)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175"

    class Config:
        env_file = ".env"


settings = Settings()
