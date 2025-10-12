"""Ollama API client for local LLM interactions."""
import httpx
from typing import Optional, Dict, Any
from .constants import LLM_TIMEOUT_SECONDS, LLM_CONNECTION_CHECK_TIMEOUT


class OllamaClient:
    """Client for interacting with local Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = LLM_TIMEOUT_SECONDS
        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    @property
    def sync_client(self) -> httpx.Client:
        """Get or create reusable synchronous HTTP client."""
        if self._sync_client is None:
            self._sync_client = httpx.Client(timeout=self.timeout)
        return self._sync_client

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Get or create reusable asynchronous HTTP client."""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self._async_client

    def close(self) -> None:
        """Close HTTP clients."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        if self._async_client:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._async_client.aclose())
                else:
                    loop.run_until_complete(self._async_client.aclose())
            except RuntimeError:
                pass
            self._async_client = None

    def __del__(self):
        """Clean up clients on deletion."""
        self.close()

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text using Ollama API."""
        url = f"{self.base_url}/api/generate"

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            response = await self.async_client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}") from e

    def generate_sync(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Synchronous version of generate."""
        url = f"{self.base_url}/api/generate"

        payload: Dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if system:
            payload["system"] = system

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            response = self.sync_client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except httpx.HTTPError as e:
            raise RuntimeError(f"Ollama API error: {e}") from e

    async def check_connection(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            url = f"{self.base_url}/api/tags"
            # Use a short timeout client for connection checks
            async with httpx.AsyncClient(timeout=LLM_CONNECTION_CHECK_TIMEOUT) as client:
                response = await client.get(url)
                return response.status_code == 200
        except (httpx.HTTPError, httpx.RequestError):
            return False

    def check_connection_sync(self) -> bool:
        """Synchronous version of check_connection."""
        try:
            url = f"{self.base_url}/api/tags"
            # Use a short timeout client for connection checks
            with httpx.Client(timeout=LLM_CONNECTION_CHECK_TIMEOUT) as client:
                response = client.get(url)
                return response.status_code == 200
        except (httpx.HTTPError, httpx.RequestError):
            return False
