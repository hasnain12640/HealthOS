from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = "sqlite:///./healthos.db"
    AI_PROVIDER: str = "mock"
    QWEN_API_KEY: str = ""
    QWEN_MODEL: str = "qwen-plus"
    QWEN_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    # Authentication
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days

    # Demo account (optional; seeding skipped if DEMO_PASSWORD is empty)
    DEMO_EMAIL: str = "demo@healthos.pk"
    DEMO_PASSWORD: str = ""
    SEED_DEMO_DATA: bool = True

    # CORS (comma-separated origins)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174,http://localhost:5175,http://127.0.0.1:5175"

    class Config:
        env_file = ".env"


settings = Settings()
