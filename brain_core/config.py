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
        AZURE_OPENAI_API_KEY: Azure OpenAI API key
        AZURE_OPENAI_ENDPOINT: Azure OpenAI endpoint URL
        AZURE_SEARCH_ENDPOINT: Azure AI Search service endpoint URL
        AZURE_SEARCH_API_KEY: Azure AI Search API key

    Optional environment variables:
        AZURE_OPENAI_DEPLOYMENT: Azure OpenAI deployment name (default: "gpt-4o")
        AZURE_OPENAI_API_VERSION: Azure OpenAI API version (default: "2024-02-15-preview")
        AZURE_SEARCH_INDEX_NAME: Search index name (default: "second-brain-notes")
        BRAIN_COST_DB_PATH: Path to cost tracking database (default: ~/.brain/costs.db)
        BRAIN_LOG_LEVEL: Logging level - DEBUG, INFO, WARNING, ERROR (default: INFO)
        BRAIN_LOG_FILE: Path to log file (optional, logs to console if not set)
    """

    def __init__(self, env_file: Path | None = None, validate_paths: bool = True):
        """Load configuration from .env file.

        Args:
            env_file: Optional path to .env file. If None, loads from default location.
            validate_paths: If True, validates that paths exist. Set to False for testing.
        """
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

        # Validate paths exist (can be disabled for testing)
        if validate_paths:
            if not self.diary_path.exists():
                raise ValueError(f"DIARY_PATH does not exist: {self.diary_path}")
            if not self.planner_path.exists():
                raise ValueError(f"PLANNER_PATH does not exist: {self.planner_path}")

        # Azure OpenAI configuration (required)
        self.azure_api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not self.azure_api_key:
            raise ValueError("AZURE_OPENAI_API_KEY must be set in .env")

        self.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        if not self.azure_endpoint:
            raise ValueError("AZURE_OPENAI_ENDPOINT must be set in .env")

        self.azure_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
        self.azure_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

        # Azure Search configuration (required for notes search)
        azure_search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        if not azure_search_endpoint:
            raise ValueError("AZURE_SEARCH_ENDPOINT must be set in .env")

        azure_search_api_key = os.getenv("AZURE_SEARCH_API_KEY")
        if not azure_search_api_key:
            raise ValueError("AZURE_SEARCH_API_KEY must be set in .env")

        self.azure_search_endpoint = azure_search_endpoint
        self.azure_search_api_key = azure_search_api_key
        self.azure_search_index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "second-brain-notes")

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
        Configured Azure OpenAI LLM client.

    Raises:
        ValueError: If Azure OpenAI credentials are not configured.
    """
    from .azure_openai_client import AzureOpenAIClient

    if config is None:
        config = get_config()

    if not config.azure_api_key or not config.azure_endpoint:
        raise ValueError(
            "Azure OpenAI credentials required. Set AZURE_OPENAI_API_KEY and "
            "AZURE_OPENAI_ENDPOINT in .env"
        )

    return AzureOpenAIClient(
        api_key=config.azure_api_key,
        endpoint=config.azure_endpoint,
        deployment_name=config.azure_deployment,
        api_version=config.azure_api_version,
    )


def get_azure_search_client(config: Config | None = None):
    """Get the Azure Search client based on configuration.

    Args:
        config: Optional Config instance. If None, uses cached global config.
                Useful for testing with custom configurations.

    Returns:
        Configured Azure Search client for notes search.
    """
    from .notes_search_client import AzureSearchNotesClient

    if config is None:
        config = get_config()

    return AzureSearchNotesClient(
        endpoint=config.azure_search_endpoint,
        api_key=config.azure_search_api_key,
        index_name=config.azure_search_index_name,
    )
