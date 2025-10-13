"""Azure AI Search client for querying book notes."""
from typing import List
from dataclasses import dataclass

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient


@dataclass
class SearchResult:
    """A single search result from Azure AI Search."""
    id: str
    title: str
    content: str
    source: str
    category: str
    file_name: str
    word_count: int
    score: float
    created_at: str
    metadata: dict


class AzureSearchNotesClient:
    """Client for searching book notes using Azure AI Search."""

    def __init__(
        self,
        endpoint: str,
        api_key: str,
        index_name: str
    ):
        """Initialize the Azure Search client.

        Args:
            endpoint: Azure Search service endpoint
            api_key: Azure Search API key
            index_name: Name of the search index
        """
        self.endpoint = endpoint
        self.index_name = index_name

        credential = AzureKeyCredential(api_key)
        self.client = SearchClient(
            endpoint=endpoint,
            index_name=index_name,
            credential=credential
        )

    def search(
        self,
        query: str,
        top: int = 10,
        search_mode: str = "any"
    ) -> List[SearchResult]:
        """Perform a text search on the notes index.

        Args:
            query: Search query text
            top: Maximum number of results to return
            search_mode: "any" or "all" - how to match query terms

        Returns:
            List of SearchResult objects
        """
        results = self.client.search(
            search_text=query,
            top=top,
            search_mode=search_mode,
            include_total_count=True
        )

        search_results = []
        for result in results:
            search_results.append(SearchResult(
                id=result.get("id", ""),
                title=result.get("title", "Untitled"),
                content=result.get("content", ""),
                source=result.get("source", "Unknown"),
                category=result.get("category", ""),
                file_name=result.get("file_name", ""),
                word_count=result.get("word_count", 0),
                score=result.get("@search.score", 0.0),
                created_at=result.get("created_at", ""),
                metadata={k: v for k, v in result.items() if not k.startswith("@")}
            ))

        return search_results

    def semantic_search(
        self,
        query: str,
        top: int = 10
    ) -> List[SearchResult]:
        """Perform a semantic search using Azure's semantic ranking.

        Args:
            query: Search query text
            top: Maximum number of results to return

        Returns:
            List of SearchResult objects with semantic relevance
        """
        results = self.client.search(
            search_text=query,
            top=top,
            query_type="semantic",
            semantic_configuration_name="default",
            include_total_count=True
        )

        search_results = []
        for result in results:
            search_results.append(SearchResult(
                id=result.get("id", ""),
                title=result.get("title", "Untitled"),
                content=result.get("content", ""),
                source=result.get("source", "Unknown"),
                category=result.get("category", ""),
                file_name=result.get("file_name", ""),
                word_count=result.get("word_count", 0),
                score=result.get("@search.reranker_score", result.get("@search.score", 0.0)),
                created_at=result.get("created_at", ""),
                metadata={k: v for k, v in result.items() if not k.startswith("@")}
            ))

        return search_results

    def check_connection(self) -> bool:
        """Check if the connection to Azure Search is valid.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Try to get document count as a simple health check
            results = self.client.search(search_text="*", top=1)
            list(results)  # Execute the query
            return True
        except Exception:
            return False



