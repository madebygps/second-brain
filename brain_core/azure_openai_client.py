"""Azure OpenAI client for cloud LLM interactions."""
from typing import Optional
import time
import logging
from openai import AzureOpenAI
from .llm_client import LLMClient
from .cost_tracker import get_cost_tracker
from .logging_config import log_llm_call

logger = logging.getLogger(__name__)


class AzureOpenAIClient(LLMClient):
    """Client for interacting with Azure OpenAI API."""

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        deployment_name: str,
        api_version: str = "2024-02-15-preview"
    ):
        self.client = AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        self.deployment_name = deployment_name

    def generate_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        operation: str = "generate",
        entry_date: Optional[str] = None
    ) -> str:
        """Generate text using Azure OpenAI API.
        
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
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            elapsed_seconds = time.time() - start_time
            
            # Extract response text and usage information
            response_text = response.choices[0].message.content or ""
            usage = response.usage
            if usage:
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
                total_tokens = usage.total_tokens
                
                # Track costs
                cost_tracker = get_cost_tracker()
                estimated_cost = cost_tracker.calculate_cost(
                    self.deployment_name, prompt_tokens, completion_tokens
                )
                
                # Prepare metadata
                metadata = {
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "prompt_length": len(prompt),
                    "response_length": len(response_text),
                    "system_prompt_length": len(system) if system else 0
                }
                
                # Record usage
                cost_tracker.record_usage(
                    operation=operation,
                    model=self.deployment_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    elapsed_seconds=elapsed_seconds,
                    entry_date=entry_date,
                    metadata=metadata
                )
                
                # Log LLM call details
                log_llm_call(
                    operation=operation,
                    model=self.deployment_name,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=total_tokens,
                    elapsed_seconds=elapsed_seconds,
                    cost_estimate=estimated_cost
                )
            else:
                logger.warning(f"No usage information returned from {operation} operation")

            return response_text
            
        except Exception as e:
            elapsed_seconds = time.time() - start_time
            logger.error(f"Azure OpenAI API error in {operation} after {elapsed_seconds:.2f}s: {e}")
            raise RuntimeError(f"Azure OpenAI API error: {e}") from e

    def check_connection_sync(self) -> bool:
        """Check if Azure OpenAI is accessible."""
        try:
            # Make a minimal request to test connection
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the client (Azure SDK handles cleanup automatically)."""
        pass
