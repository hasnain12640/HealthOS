from app.core.config import settings
from app.services.ai.base_provider import BaseAIProvider


def get_provider() -> BaseAIProvider:
    if settings.AI_PROVIDER == "qwen":
        from app.services.ai.qwen_provider import QwenProvider
        return QwenProvider()
    from app.services.ai.mock_provider import MockProvider
    return MockProvider()
