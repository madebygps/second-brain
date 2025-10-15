"""Unified OpenAI client for both Azure OpenAI and Ollama."""

import logging
import time

from openai import AzureOpenAI, OpenAI

from .cost_tracker import get_cost_tracker
from .llm_client import LLMClient
from .logging_config import log_llm_call

logger = logging.getLogger(__name__)


class UnifiedOpenAIClient(LLMClient):
    """Client for OpenAI-compatible APIs (Azure OpenAI, Ollama)."""

    def __init__(
        self,
        provider: str,
        api_key: str | None = None,
        endpoint: str | None = None,
        deployment_name: str | None = None,
        api_version: str = "2024-02-15-preview",
        base_url: str | None = None,
        model: str | None = None,
    ):
        """Initialize OpenAI client for Azure or Ollama.

        Args:
            provider: "azure" or "ollama"
            api_key: API key (required for Azure, ignored for Ollama)
            endpoint: Azure endpoint (required for Azure)
            deployment_name: Azure deployment name (required for Azure)
            api_version: Azure API version
            base_url: Ollama base URL (required for Ollama)
            model: Model name (required for Ollama)
        """
        self.provider = provider

        if provider == "azure":
            if not api_key or not endpoint or not deployment_name:
                raise ValueError("Azure provider requires api_key, endpoint, and deployment_name")
            self.client = AzureOpenAI(
                api_key=api_key, azure_endpoint=endpoint, api_version=api_version
            )
            self.model = deployment_name
        elif provider == "ollama":
            if not base_url or not model:
                raise ValueError("Ollama provider requires base_url and model")
            # Normalize base_url - remove trailing slash and /v1 if present
            normalized_url = base_url.rstrip("/").removesuffix("/v1")
            self.client = OpenAI(
                base_url=f"{normalized_url}/v1",
                api_key="ollama",  # Ollama doesn't need a real key
            )
            self.model = model
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def generate_sync(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        operation: str = "generate",
        entry_date: str | None = None,
    ) -> str:
        """Generate text using OpenAI-compatible API.

        Args:
            prompt: User prompt text
            system: System message (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            operation: Type of operation for cost tracking (backlinks, tags, etc.)
            entry_date: Date of diary entry being processed (for cost tracking)

        Returns:
            Generated text response
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            elapsed_seconds = time.time() - start_time

            # Extract response text and usage information
            response_text = response.choices[0].message.content or ""
            usage = response.usage

            if usage:
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
                total_tokens = usage.total_tokens

                # Calculate cost (only for Azure)
                estimated_cost = 0.0
                if self.provider == "azure":
                    cost_tracker = get_cost_tracker()
                    estimated_cost = cost_tracker.calculate_cost(
                        self.model, prompt_tokens, completion_tokens
                    )

                    # Prepare metadata
                    metadata = {
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "prompt_length": len(prompt),
                        "response_length": len(response_text),
                        "system_prompt_length": len(system) if system else 0,
                    }

                    # Record usage
                    cost_tracker.record_usage(
                        operation=operation,
                        model=self.model,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        elapsed_seconds=elapsed_seconds,
                        entry_date=entry_date,
                        metadata=metadata,
                    )

                # Log LLM call details
                log_llm_call(
                    operation=operation,
                    model=self.model,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    elapsed_seconds=elapsed_seconds,
                    cost_estimate=estimated_cost,
                )
            else:
                logger.warning(f"No usage information returned from {operation} operation")

            return response_text

        except Exception as e:
            elapsed_seconds = time.time() - start_time
            logger.error(f"LLM API error in {operation} after {elapsed_seconds:.2f}s: {e}")
            raise RuntimeError(f"LLM API error: {e}") from e

    def check_connection_sync(self) -> bool:
        """Check if LLM service is accessible."""
        try:
            # Make a minimal request to test connection
            self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            logger.info(f"{self.provider.title()} connection successful (model: {self.model})")
            return True
        except Exception as e:
            logger.error(f"{self.provider.title()} connection failed: {e}")
            return False

    def close(self) -> None:
        """Close the client (OpenAI SDK handles cleanup automatically)."""
        pass


# Keep old class name for backwards compatibility
AzureOpenAIClient = UnifiedOpenAIClient
