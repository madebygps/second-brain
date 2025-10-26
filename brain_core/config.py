"""Configuration management for diary system."""

import os
from collections.abc import Callable
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


def _get_required_env(key: str, error_context: str = "") -> str:
    """Get required environment variable or raise clear error.

    Args:
        key: Environment variable name
        error_context: Additional context for error message

    Returns:
        Value of environment variable

    Raises:
        ValueError: If environment variable is not set
    """
    value = os.getenv(key)
    if not value:
        error_msg = f"{key} must be set in .env"
        if error_context:
            error_msg += f" {error_context}"
        raise ValueError(error_msg)
    return value


def _get_optional_env(key: str, default: str) -> str:
    """Get optional environment variable with default.

    Args:
        key: Environment variable name
        default: Default value if not set

    Returns:
        Value of environment variable or default
    """
    return os.getenv(key, default)


def _get_choice_env(
    key: str,
    allowed_choices: list[str],
    default: str,
    transform: Callable[[str], str] = str.lower,
) -> str:
    """Get environment variable and validate against allowed choices.

    Args:
        key: Environment variable name
        allowed_choices: List of valid values
        default: Default value if not set
        transform: Optional transformation function (e.g., str.lower)

    Returns:
        Validated and transformed value

    Raises:
        ValueError: If value is not in allowed choices
    """
    value = transform(os.getenv(key, default))
    if value not in allowed_choices:
        choices_str = "', '".join(allowed_choices)
        raise ValueError(f"{key} must be one of ['{choices_str}'], got: {value}")
    return value


def _load_env_from_locations(env_file: Path | None = None) -> bool:
    """Load environment variables from .env file in standard locations.

    Args:
        env_file: Optional explicit path to .env file

    Returns:
        True if .env file was found and loaded, False otherwise
    """
    if env_file:
        load_dotenv(env_file)
        return True

    # Search for .env in standard locations (in priority order)
    env_locations = [
        Path.cwd() / ".env",  # Current directory (highest priority)
        Path.home() / ".config" / "brain" / ".env",  # XDG config dir
    ]

    for env_path in env_locations:
        if _try_load_dotenv_from_path(env_path):
            return True

    # Try default load_dotenv() which searches up the directory tree
    load_dotenv()
    return False  # Unknown if found, but we tried


def _try_load_dotenv_from_path(env_path: Path) -> bool:
    """Attempt to load .env from a specific path.

    Args:
        env_path: Path to .env file

    Returns:
        True if file was loaded successfully, False otherwise
    """
    try:
        resolved_path = env_path.resolve(strict=False)
        # Security: Only load if file is readable and is a regular file
        if resolved_path.exists() and resolved_path.is_file():
            load_dotenv(resolved_path)
            return True
    except (OSError, RuntimeError):
        # Skip paths that can't be resolved (permission issues, etc.)
        pass
    return False


def _get_validated_path(key: str, validate: bool = True) -> Path:
    """Get path from environment and optionally validate it exists.

    Args:
        key: Environment variable name
        validate: If True, validate that path exists

    Returns:
        Path object

    Raises:
        ValueError: If path is not set or doesn't exist (when validate=True)
    """
    path_str = os.getenv(key)
    if not path_str:
        if key == "DIARY_PATH":
            raise ValueError(
                "DIARY_PATH must be set in .env file.\n"
                "Create .env file in one of these locations:\n"
                f"  - {Path.home() / '.config' / 'brain' / '.env'} (recommended)\n"
                f"  - {Path.home() / '.brain' / '.env'}\n"
                f"  - {Path.cwd() / '.env'}\n"
                "See SETUP_CHECKLIST.md for configuration guide."
            )
        raise ValueError(f"{key} must be set in .env")

    path = Path(path_str)
    if validate and not path.exists():
        raise ValueError(f"{key} does not exist: {path}")
    return path


def _get_azure_config() -> dict[str, str]:
    """Get Azure OpenAI configuration from environment.

    Returns:
        Dictionary with Azure config keys

    Raises:
        ValueError: If required Azure credentials are missing
    """
    api_key = _get_required_env(
        "AZURE_OPENAI_API_KEY",
        "when LLM_PROVIDER=azure",
    )
    endpoint = _get_required_env(
        "AZURE_OPENAI_ENDPOINT",
        "when LLM_PROVIDER=azure",
    )
    deployment = _get_optional_env("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    api_version = _get_optional_env("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    return {
        "api_key": api_key,
        "endpoint": endpoint,
        "deployment": deployment,
        "api_version": api_version,
    }


def _get_ollama_config() -> dict[str, str]:
    """Get Ollama configuration from environment.

    Returns:
        Dictionary with Ollama config keys
    """
    base_url = _get_optional_env("OLLAMA_BASE_URL", "http://localhost:11434")
    model = _get_optional_env("OLLAMA_MODEL", "llama3.1")

    return {
        "base_url": base_url,
        "model": model,
    }


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
        # Load environment variables from .env file
        _load_env_from_locations(env_file)

        # Load required paths
        self.diary_path = _get_validated_path("DIARY_PATH", validate=validate_paths)
        self.planner_path = _get_validated_path("PLANNER_PATH", validate=validate_paths)

        # Load LLM provider configuration
        self.llm_provider = _get_choice_env(
            "LLM_PROVIDER",
            allowed_choices=["azure", "ollama"],
            default="azure",
            transform=str.lower,
        )

        # Load provider-specific configuration
        if self.llm_provider == "azure":
            azure_config = _get_azure_config()
            self.azure_api_key = azure_config["api_key"]
            self.azure_endpoint = azure_config["endpoint"]
            self.azure_deployment = azure_config["deployment"]
            self.azure_api_version = azure_config["api_version"]
            # Set Ollama to None when using Azure
            self.ollama_base_url = None
            self.ollama_model = None
        else:
            # Using Ollama
            ollama_config = _get_ollama_config()
            self.ollama_base_url = ollama_config["base_url"]
            self.ollama_model = ollama_config["model"]
            # Set Azure to None when using Ollama
            self.azure_api_key = None
            self.azure_endpoint = None
            self.azure_deployment = None
            self.azure_api_version = "2025-01-01-preview"  # Keep default for consistency

        # Load optional configuration
        self.cost_db_path = os.getenv("BRAIN_COST_DB_PATH")  # Default handled in CostTracker
        self.log_level = _get_optional_env("BRAIN_LOG_LEVEL", "INFO")
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
