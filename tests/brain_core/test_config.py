"""Tests for config module - Only essential configuration validation."""

from unittest.mock import patch

import pytest

from brain_core.config import Config


class TestConfig:
    """Essential configuration tests to prevent data loss and misconfiguration."""

    def test_config_missing_diary_path(self, monkeypatch, temp_dir):
        """Test config raises error when DIARY_PATH is missing - prevents data loss."""
        with patch("brain_core.config.load_dotenv"):
            monkeypatch.delenv("DIARY_PATH", raising=False)
            monkeypatch.setenv("PLANNER_PATH", "/tmp/planner")

            with pytest.raises(ValueError, match="DIARY_PATH must be set"):
                Config(validate_paths=False)

    def test_config_missing_planner_path(self, monkeypatch, temp_dir):
        """Test config raises error when PLANNER_PATH is missing - prevents data loss."""
        with patch("brain_core.config.load_dotenv"):
            monkeypatch.setenv("DIARY_PATH", str(temp_dir))
            monkeypatch.delenv("PLANNER_PATH", raising=False)

            with pytest.raises(ValueError, match="PLANNER_PATH must be set"):
                Config(validate_paths=False)
