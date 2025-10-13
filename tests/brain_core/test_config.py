"""Tests for config module."""
import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from brain_core.config import Config, get_llm_client, clear_config_cache


class TestConfig:
    """Tests for Config class."""

    def test_config_with_valid_env(self, mock_env):
        """Test config loads successfully with valid environment."""
        # Config is already set up in mock_env fixture
        config = Config(validate_paths=False)

        assert config.diary_path == mock_env["diary_path"]
        assert config.planner_path == mock_env["planner_path"]
        assert config.azure_api_key == "test-openai-key"
        assert config.azure_endpoint == "https://test.openai.azure.com/"
        assert config.azure_deployment == "gpt-4"

    def test_config_missing_diary_path(self, monkeypatch, temp_dir):
        """Test config raises error when DIARY_PATH is missing."""
        # Patch load_dotenv to prevent loading from any .env file
        with patch('brain_core.config.load_dotenv'):
            monkeypatch.delenv("DIARY_PATH", raising=False)
            monkeypatch.setenv("PLANNER_PATH", "/tmp/planner")

            with pytest.raises(ValueError, match="DIARY_PATH must be set"):
                Config(validate_paths=False)

    def test_config_missing_planner_path(self, monkeypatch, temp_dir):
        """Test config raises error when PLANNER_PATH is missing."""
        # Patch load_dotenv to prevent loading from any .env file
        with patch('brain_core.config.load_dotenv'):
            monkeypatch.setenv("DIARY_PATH", str(temp_dir))
            monkeypatch.delenv("PLANNER_PATH", raising=False)

            with pytest.raises(ValueError, match="PLANNER_PATH must be set"):
                Config(validate_paths=False)

    def test_config_validates_paths_when_enabled(self, monkeypatch, temp_dir):
        """Test config validates that paths exist when validation is enabled."""
        nonexistent_path = temp_dir / "does_not_exist"
        monkeypatch.setenv("DIARY_PATH", str(nonexistent_path))
        monkeypatch.setenv("PLANNER_PATH", str(temp_dir))

        with pytest.raises(ValueError, match="DIARY_PATH does not exist"):
            Config(validate_paths=True)

    def test_config_skips_validation_when_disabled(self, monkeypatch, temp_dir):
        """Test config skips path validation when disabled."""
        nonexistent_path = temp_dir / "does_not_exist"
        monkeypatch.setenv("DIARY_PATH", str(nonexistent_path))
        monkeypatch.setenv("PLANNER_PATH", str(temp_dir))

        # Should not raise error
        config = Config(validate_paths=False)
        assert config.diary_path == nonexistent_path

    def test_config_defaults(self, mock_env):
        """Test config sets appropriate defaults."""
        config = Config(validate_paths=False)

        # Azure OpenAI is now required
        assert config.azure_api_key == "test-openai-key"
        assert config.azure_endpoint == "https://test.openai.azure.com/"
        assert config.azure_deployment == "gpt-4"
        assert config.azure_api_version == "2024-02-15-preview"

    def test_config_azure_settings(self, monkeypatch, mock_env):
        """Test config loads Azure settings correctly."""
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "custom-key")
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://custom.openai.azure.com/")
        monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

        config = Config(validate_paths=False)

        assert config.azure_api_key == "custom-key"
        assert config.azure_endpoint == "https://custom.openai.azure.com/"
        assert config.azure_deployment == "gpt-4o"

    def test_config_azure_search_settings(self, mock_env):
        """Test config loads Azure Search settings correctly."""
        config = Config(validate_paths=False)

        assert config.azure_search_endpoint == "https://test.search.windows.net"
        assert config.azure_search_api_key == "test-search-key"
        assert config.azure_search_index_name == "test-index"

    def test_config_missing_azure_search_endpoint(self, monkeypatch, temp_dir):
        """Test config raises error when AZURE_SEARCH_ENDPOINT is missing."""
        with patch('brain_core.config.load_dotenv'):
            monkeypatch.setenv("DIARY_PATH", str(temp_dir))
            monkeypatch.setenv("PLANNER_PATH", str(temp_dir))
            monkeypatch.delenv("AZURE_SEARCH_ENDPOINT", raising=False)
            monkeypatch.setenv("AZURE_SEARCH_API_KEY", "test-key")

            with pytest.raises(ValueError, match="AZURE_SEARCH_ENDPOINT must be set"):
                Config(validate_paths=False)

    def test_config_missing_azure_search_api_key(self, monkeypatch, temp_dir):
        """Test config raises error when AZURE_SEARCH_API_KEY is missing."""
        with patch('brain_core.config.load_dotenv'):
            monkeypatch.setenv("DIARY_PATH", str(temp_dir))
            monkeypatch.setenv("PLANNER_PATH", str(temp_dir))
            monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://test.search.windows.net")
            monkeypatch.delenv("AZURE_SEARCH_API_KEY", raising=False)

            with pytest.raises(ValueError, match="AZURE_SEARCH_API_KEY must be set"):
                Config(validate_paths=False)

    def test_config_azure_search_default_index_name(self, monkeypatch, temp_dir):
        """Test config uses default index name when not specified."""
        with patch('brain_core.config.load_dotenv'):
            monkeypatch.setenv("DIARY_PATH", str(temp_dir))
            monkeypatch.setenv("PLANNER_PATH", str(temp_dir))
            monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://test.search.windows.net")
            monkeypatch.setenv("AZURE_SEARCH_API_KEY", "test-key")
            monkeypatch.delenv("AZURE_SEARCH_INDEX_NAME", raising=False)

            config = Config(validate_paths=False)
            assert config.azure_search_index_name == "second-brain-notes"


class TestGetLLMClient:
    """Tests for get_llm_client factory function."""

    def test_get_llm_client_azure(self, mock_env):
        """Test get_llm_client returns AzureOpenAIClient."""
        clear_config_cache()  # Clear any cached config
        config = Config(validate_paths=False)

        client = get_llm_client(config)

        # Should return an AzureOpenAIClient
        assert client is not None
        assert hasattr(client, 'generate_sync')
        assert hasattr(client, 'check_connection_sync')

    def test_get_llm_client_missing_credentials(self, monkeypatch, mock_env):
        """Test Config raises error when Azure credentials are missing."""
        monkeypatch.setenv("AZURE_OPENAI_API_KEY", "")  # Empty key
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "")  # Empty endpoint

        with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY must be set in .env"):
            config = Config(validate_paths=False)

    def test_get_llm_client_uses_cached_config_by_default(self, mock_env):
        """Test get_llm_client uses cached config when no config is provided."""
        clear_config_cache()

        # Should use cached config internally
        client = get_llm_client()
        assert client is not None

    def test_get_llm_client_accepts_custom_config(self, mock_env):
        """Test get_llm_client accepts custom config for testing."""
        # Create a custom config
        custom_config = Config(validate_paths=False)

        # Pass custom config
        client = get_llm_client(custom_config)
        assert client is not None
