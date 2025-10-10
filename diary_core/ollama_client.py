"""Ollama API client for local LLM interactions."""
import httpx
from typing import Optional, Dict, Any


class OllamaClient:
    """Client for interacting with local Ollama API."""

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:latest"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = 300.0  # 5 minutes for LLM responses

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

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

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

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

    async def check_connection(self) -> bool:
        """Check if Ollama is running and accessible."""
        try:
            url = f"{self.base_url}/api/tags"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    def check_connection_sync(self) -> bool:
        """Synchronous version of check_connection."""
        try:
            url = f"{self.base_url}/api/tags"
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                return response.status_code == 200
        except Exception:
            return False
