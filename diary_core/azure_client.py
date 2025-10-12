"""Azure OpenAI client for cloud LLM interactions."""
from typing import Optional
from openai import AzureOpenAI
from .llm_client import LLMClient


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
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text using Azure OpenAI API."""
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content or ""
        except Exception as e:
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
