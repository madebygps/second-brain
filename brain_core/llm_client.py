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
        max_tokens: Optional[int] = None,
        operation: str = "generate",
        entry_date: Optional[str] = None
    ) -> str:
        """Generate text synchronously.
        
        Args:
            prompt: User prompt text
            system: System message (optional)
            temperature: Sampling temperature (0.0-2.0)
            max_tokens: Maximum tokens to generate
            operation: Type of operation for tracking (e.g., 'task_extraction', 'semantic_backlinks')
            entry_date: Date of diary entry being processed (YYYY-MM-DD format)
            
        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def check_connection_sync(self) -> bool:
        """Check if the LLM service is accessible."""
        pass

    def close(self) -> None:
        """Close any open connections (optional)."""
        pass
