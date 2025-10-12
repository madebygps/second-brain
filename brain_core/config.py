"""Configuration management for diary system."""
from pathlib import Path
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv
import os


class Config:
    """Configuration loaded from .env file."""

    def __init__(self, env_file: Optional[Path] = None):
        """Load configuration from .env file."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Required paths
        diary_path = os.getenv("DIARY_PATH")
        if not diary_path:
            raise ValueError("DIARY_PATH must be set in .env")

        planner_path = os.getenv("PLANNER_PATH")
        if not planner_path:
            raise ValueError("PLANNER_PATH must be set in .env")

        self.diary_path = Path(diary_path)
        self.planner_path = Path(planner_path)

        # Validate paths exist
        if not self.diary_path.exists():
            raise ValueError(f"DIARY_PATH does not exist: {self.diary_path}")
        if not self.planner_path.exists():
            raise ValueError(f"PLANNER_PATH does not exist: {self.planner_path}")

        # LLM Provider configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()  # "ollama" or "azure"

        # Ollama configuration
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

        # Azure OpenAI configuration
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        # Daemon configuration
        self.daemon_auto_link_time = os.getenv("DAEMON_AUTO_LINK_TIME", "23:00")
        self.daemon_weekly_analysis = os.getenv("DAEMON_WEEKLY_ANALYSIS", "true").lower() == "true"
        self.daemon_refresh_days = int(os.getenv("DAEMON_REFRESH_DAYS", "30"))


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get or create global config instance (cached)."""
    return Config()


def clear_config_cache() -> None:
    """Clear cached config (useful for testing)."""
    get_config.cache_clear()


def get_llm_client():
    """Get the appropriate LLM client based on configuration."""
    from .llm_client import LLMClient
    from .ollama_client import OllamaClient
    from .azure_client import AzureOpenAIClient

    config = get_config()

    if config.llm_provider == "azure":
        if not config.azure_api_key or not config.azure_endpoint:
            raise ValueError(
                "Azure OpenAI is selected but AZURE_OPENAI_API_KEY or "
                "AZURE_OPENAI_ENDPOINT is not set in .env"
            )
        return AzureOpenAIClient(
            api_key=config.azure_api_key,
            endpoint=config.azure_endpoint,
            deployment_name=config.azure_deployment,
            api_version=config.azure_api_version
        )
    else:
        # Default to Ollama
        return OllamaClient(config.ollama_url, config.ollama_model)
