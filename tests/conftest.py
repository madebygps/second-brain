"""Shared test fixtures."""
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from datetime import date


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
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:latest")
    monkeypatch.setenv("OLLAMA_URL", "http://localhost:11434")

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
