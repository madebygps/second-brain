"""Tests for notes_search_client module."""
import pytest
from unittest.mock import Mock, patch, MagicMock

from brain_core.notes_search_client import (
    AzureSearchNotesClient,
    SearchResult
)
from brain_core.config import get_azure_search_client, Config


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        result = SearchResult(
            id="test-id",
            title="Test Title",
            content="Test content",
            source="test-source",
            category="books",
            file_name="test.jpg",
            word_count=100,
            score=1.5,
            created_at="2025-10-12",
            metadata={"key": "value"}
        )

        assert result.id == "test-id"
        assert result.title == "Test Title"
        assert result.content == "Test content"
        assert result.score == 1.5


class TestAzureSearchNotesClient:
    """Tests for AzureSearchNotesClient class."""

    @pytest.fixture
    def mock_search_client(self):
        """Mock Azure SearchClient."""
        with patch('brain_core.notes_search_client.SearchClient') as mock:
            yield mock

    @pytest.fixture
    def search_client(self, mock_search_client):
        """Create a test search client."""
        return AzureSearchNotesClient(
            endpoint="https://test.search.windows.net",
            api_key="test-key",
            index_name="test-index"
        )

    def test_initialization(self, search_client):
        """Test client initialization."""
        assert search_client.endpoint == "https://test.search.windows.net"
        assert search_client.index_name == "test-index"

    def test_search(self, search_client):
        """Test text search."""
        # Mock search results
        mock_result = {
            "id": "test-1",
            "title": "Test Book",
            "content": "Test content about discipline",
            "source": "test-book",
            "category": "books",
            "file_name": "test.jpg",
            "word_count": 50,
            "@search.score": 2.5,
            "created_at": "2025-10-12"
        }

        search_client.client.search = Mock(return_value=[mock_result])

        results = search_client.search("discipline", top=5)

        assert len(results) == 1
        assert results[0].title == "Test Book"
        assert results[0].score == 2.5
        assert results[0].content == "Test content about discipline"

        search_client.client.search.assert_called_once()

    def test_semantic_search(self, search_client):
        """Test semantic search."""
        mock_result = {
            "id": "test-1",
            "title": "Test Book",
            "content": "Semantic content",
            "source": "test-book",
            "category": "books",
            "file_name": "test.jpg",
            "word_count": 50,
            "@search.score": 2.0,
            "@search.reranker_score": 3.5,
            "created_at": "2025-10-12"
        }

        search_client.client.search = Mock(return_value=[mock_result])

        results = search_client.semantic_search("test query", top=10)

        assert len(results) == 1
        assert results[0].score == 3.5  # Should use reranker score
        search_client.client.search.assert_called_once()

    def test_check_connection_success(self, search_client):
        """Test connection check success."""
        search_client.client.search = Mock(return_value=[])

        assert search_client.check_connection() is True

    def test_check_connection_failure(self, search_client):
        """Test connection check failure."""
        search_client.client.search = Mock(side_effect=Exception("Connection error"))

        assert search_client.check_connection() is False


class TestGetAzureSearchClient:
    """Tests for get_azure_search_client factory function."""

    def test_with_valid_env(self, monkeypatch, tmp_path):
        """Test creating client with valid environment variables."""
        monkeypatch.setenv("DIARY_PATH", str(tmp_path / "diary"))
        monkeypatch.setenv("PLANNER_PATH", str(tmp_path / "planner"))
        monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://test.search.windows.net")
        monkeypatch.setenv("AZURE_SEARCH_API_KEY", "test-key")
        monkeypatch.setenv("AZURE_SEARCH_INDEX_NAME", "test-index")

        (tmp_path / "diary").mkdir()
        (tmp_path / "planner").mkdir()

        with patch('brain_core.notes_search_client.AzureSearchNotesClient') as mock_client:
            mock_client.return_value = Mock()
            config = Config(validate_paths=True)
            client = get_azure_search_client(config)
            
            mock_client.assert_called_once_with(
                endpoint="https://test.search.windows.net",
                api_key="test-key",
                index_name="test-index"
            )

    def test_with_default_index_name(self, monkeypatch, tmp_path):
        """Test default index name."""
        monkeypatch.setenv("DIARY_PATH", str(tmp_path / "diary"))
        monkeypatch.setenv("PLANNER_PATH", str(tmp_path / "planner"))
        monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://test.search.windows.net")
        monkeypatch.setenv("AZURE_SEARCH_API_KEY", "test-key")
        monkeypatch.delenv("AZURE_SEARCH_INDEX_NAME", raising=False)

        (tmp_path / "diary").mkdir()
        (tmp_path / "planner").mkdir()

        with patch('brain_core.notes_search_client.AzureSearchNotesClient') as mock_client:
            mock_client.return_value = Mock()
            config = Config(validate_paths=True)
            client = get_azure_search_client(config)
            
            mock_client.assert_called_once_with(
                endpoint="https://test.search.windows.net",
                api_key="test-key",
                index_name="second-brain-notes"
            )
