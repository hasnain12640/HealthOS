from openai import AsyncOpenAI
from app.services.ai.base_provider import BaseAIProvider
from app.core.config import settings


class QwenProvider(BaseAIProvider):
    def __init__(self):
        self._client = AsyncOpenAI(
            api_key=settings.QWEN_API_KEY,
            base_url=settings.QWEN_BASE_URL,
            timeout=60.0,
        )

    async def chat(self, messages: list[dict], system_prompt: str) -> str:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        response = await self._client.chat.completions.create(
            model=settings.QWEN_MODEL,
            messages=full_messages,
            max_tokens=600,
            temperature=0.4,
        )
        return response.choices[0].message.content or ""
