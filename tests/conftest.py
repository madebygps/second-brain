"""Shared test fixtures."""

from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env(monkeypatch, temp_dir):
    """Mock environment variables for testing."""
    diary_path = temp_dir / "diary"
    planner_path = temp_dir / "planner"
    diary_path.mkdir()
    planner_path.mkdir()

    monkeypatch.setenv("DIARY_PATH", str(diary_path))
    monkeypatch.setenv("PLANNER_PATH", str(planner_path))

    # Azure OpenAI configuration (required)
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")

    # Azure Search configuration (required)
    monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://test.search.windows.net")
    monkeypatch.setenv("AZURE_SEARCH_API_KEY", "test-search-key")
    monkeypatch.setenv("AZURE_SEARCH_INDEX_NAME", "test-index")

    return {
        "diary_path": diary_path,
        "planner_path": planner_path,
    }


@pytest.fixture
def sample_entry_content():
    """Sample diary entry content."""
    return """## Reflection Prompts
**1. What did you learn today?**
**2. What are you grateful for?**

---

## Brain Dump
Today I focused on deep work and made great progress on the project.
I learned about semantic search and how to integrate Azure AI Search.

---

## Memory Links
**Temporal:** [[2025-10-11]] • [[2025-10-10]]
**Topics:** #productivity #learning
"""


@pytest.fixture
def sample_date():
    """Sample date for testing."""
    return date(2025, 10, 12)
