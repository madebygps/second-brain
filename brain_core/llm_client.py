"""Unified LLM client interface for Azure OpenAI."""
from typing import Optional
from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def generate_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text synchronously."""
        pass

    @abstractmethod
    def check_connection_sync(self) -> bool:
        """Check if the LLM service is accessible."""
        pass

    def close(self) -> None:
        """Close any open connections (optional)."""
        pass
