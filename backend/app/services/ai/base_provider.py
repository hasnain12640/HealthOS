from abc import ABC, abstractmethod


class BaseAIProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[dict], system_prompt: str) -> str:
        """
        Send a chat turn to the provider.
        messages: list of {"role": "user"|"assistant", "content": str}
        system_prompt: full context string prepended as system role
        Returns the assistant reply text.
        """
