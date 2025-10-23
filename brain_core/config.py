"""Configuration management for diary system."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


class Config:
    """Configuration loaded from .env file.

    Required environment variables:
        DIARY_PATH: Path to Obsidian vault or markdown directory
        PLANNER_PATH: Path to planner directory for extracted todos
        LLM_PROVIDER: LLM provider to use ("azure" or "ollama", default: "azure")

    Azure OpenAI (required if LLM_PROVIDER=azure):
        AZURE_OPENAI_API_KEY: Azure OpenAI API key
        AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
        AZURE_OPENAI_DEPLOYMENT: Deployment name (default: "gpt-4o")
        AZURE_OPENAI_API_VERSION: API version (default: "2024-02-15-preview")

    Ollama (required if LLM_PROVIDER=ollama):
        OLLAMA_BASE_URL: Ollama API URL (default: "http://localhost:11434")
        OLLAMA_MODEL: Model name (default: "llama3.1")

    Optional environment variables:
        BRAIN_COST_DB_PATH: Path to cost tracking database (default: ~/.brain/costs.db)
        BRAIN_LOG_LEVEL: Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO)
        BRAIN_LOG_FILE: Path to log file (optional, logs to console if not set)
    """

    def __init__(self, env_file: Path | None = None, validate_paths: bool = True):
        """Load configuration from .env file.

        Args:
            env_file: Optional path to .env file. If None, searches standard locations.
            validate_paths: If True, validates that paths exist. Set to False for testing.
        """
        if env_file:
            load_dotenv(env_file)
        else:
            # Search for .env in standard locations (in priority order)
            env_locations = [
                Path.cwd() / ".env",  # Current directory (highest priority)
                Path.home() / ".config" / "brain" / ".env",  # XDG config dir
            ]

            env_found = False
            for env_path in env_locations:
                # Resolve symlinks and check if file exists
                try:
                    resolved_path = env_path.resolve(strict=False)
                    # Security: Only load if file is readable and is a regular file
                    if resolved_path.exists() and resolved_path.is_file():
                        load_dotenv(resolved_path)
                        env_found = True
                        break
                except (OSError, RuntimeError):
                    # Skip paths that can't be resolved (permission issues, etc.)
                    continue

            if not env_found:
                # Try default load_dotenv() which searches up the directory tree
                load_dotenv()

        # Required paths
        diary_path = os.getenv("DIARY_PATH")
        if not diary_path:
            raise ValueError(
                "DIARY_PATH must be set in .env file.\n"
                "Create .env file in one of these locations:\n"
                f"  - {Path.home() / '.config' / 'brain' / '.env'} (recommended)\n"
                f"  - {Path.home() / '.brain' / '.env'}\n"
                f"  - {Path.cwd() / '.env'}\n"
                "See SETUP_CHECKLIST.md for configuration guide."
            )

        planner_path = os.getenv("PLANNER_PATH")
        if not planner_path:
            raise ValueError("PLANNER_PATH must be set in .env")

        self.diary_path = Path(diary_path)
        self.planner_path = Path(planner_path)

        # Validate paths exist (can be disabled for testing)
        if validate_paths:
            if not self.diary_path.exists():
                raise ValueError(f"DIARY_PATH does not exist: {self.diary_path}")
            if not self.planner_path.exists():
                raise ValueError(f"PLANNER_PATH does not exist: {self.planner_path}")

        # LLM provider configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "azure").lower()
        if self.llm_provider not in ["azure", "ollama"]:
            raise ValueError(f"LLM_PROVIDER must be 'azure' or 'ollama', got: {self.llm_provider}")

        # Azure OpenAI configuration (required if using Azure)
        if self.llm_provider == "azure":
            self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
            if not self.azure_api_key:
                raise ValueError("AZURE_OPENAI_API_KEY must be set in .env when LLM_PROVIDER=azure")

            self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            if not self.azure_endpoint:
                raise ValueError(
                    "AZURE_OPENAI_ENDPOINT must be set in .env when LLM_PROVIDER=azure"
                )

            self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
            self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        else:
            # Set defaults for Azure when using Ollama (for optional Azure features)
            self.azure_api_key = None
            self.azure_endpoint = None
            self.azure_deployment = None
            self.azure_api_version = None

        # Ollama configuration (required if using Ollama)
        if self.llm_provider == "ollama":
            self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1")
        else:
            self.ollama_base_url = None
            self.ollama_model = None

        # Cost tracking configuration (optional)
        self.cost_db_path = os.getenv("BRAIN_COST_DB_PATH")  # Default handled in CostTracker

        # Logging configuration (optional)
        self.log_level = os.getenv("BRAIN_LOG_LEVEL", "INFO")
        self.log_file = os.getenv("BRAIN_LOG_FILE")  # Optional file logging


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Get or create global config instance (cached)."""
    return Config()


def clear_config_cache() -> None:
    """Clear cached config (useful for testing)."""
    get_config.cache_clear()


def get_llm_client(config: Config | None = None):
    """Get the appropriate LLM client based on configuration.

    Args:
        config: Optional Config instance. If None, uses cached global config.
                Useful for testing with custom configurations.

    Returns:
        Configured LLM client (Azure OpenAI or Ollama).

    Raises:
        ValueError: If required credentials are not configured.
    """
    if config is None:
        config = get_config()

    from .openai_client import UnifiedOpenAIClient

    if config.llm_provider == "azure":
        if not config.azure_api_key or not config.azure_endpoint:
            raise ValueError(
                "Azure OpenAI credentials required. Set AZURE_OPENAI_API_KEY and "
                "AZURE_OPENAI_ENDPOINT in .env, or set LLM_PROVIDER=ollama to use local LLM"
            )

        return UnifiedOpenAIClient(
            provider="azure",
            api_key=config.azure_api_key,
            endpoint=config.azure_endpoint,
            deployment_name=config.azure_deployment,
            api_version=config.azure_api_version,
        )

    elif config.llm_provider == "ollama":
        return UnifiedOpenAIClient(
            provider="ollama",
            base_url=config.ollama_base_url,
            model=config.ollama_model,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {config.llm_provider}")
