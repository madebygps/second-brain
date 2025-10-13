"""Azure AI Search client for querying book notes."""

from dataclasses import dataclass

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery


@dataclass
class SearchResult:
    """A single search result from Azure AI Search."""

    id: str
    title: str
    content: str
    source: str
    category: str
    file_path: str
    score: float
    metadata: dict


class AzureSearchNotesClient:
    """Client for searching book notes using Azure AI Search."""

    def __init__(self, endpoint: str, api_key: str, index_name: str):
        """Initialize the Azure Search client.

        Args:
            endpoint: Azure Search service endpoint
            api_key: Azure Search API key
            index_name: Name of the search index
        """
        self.endpoint = endpoint
        self.index_name = index_name

        credential = AzureKeyCredential(api_key)
        self.client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

    def search(self, query: str, top: int = 10, search_mode: str = "any") -> list[SearchResult]:
        """Perform a text search on the notes index.

        Args:
            query: Search query text
            top: Maximum number of results to return
            search_mode: "any" or "all" - how to match query terms

        Returns:
            List of SearchResult objects
        """
        results = self.client.search(
            search_text=query, top=top, search_mode=search_mode, include_total_count=True
        )

        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    id=result.get("id", ""),
                    title=result.get("title", "Untitled"),
                    content=result.get("content", ""),
                    source=result.get("source", "Unknown"),
                    category=result.get("category", ""),
                    file_path=result.get("file_path", ""),
                    score=result.get("@search.score", 0.0),
                    metadata={k: v for k, v in result.items() if not k.startswith("@")},
                )
            )

        return search_results

    def vector_search(
        self, query_vector: list[float], top: int = 10, text_query: str | None = None
    ) -> list[SearchResult]:
        """Perform a vector search using embeddings.

        Args:
            query_vector: Query embedding vector (384 dimensions for text-embedding-3-small)
            top: Maximum number of results to return
            text_query: Optional text query for hybrid search

        Returns:
            List of SearchResult objects with vector similarity
        """
        vector_query = VectorizedQuery(
            vector=query_vector, k_nearest_neighbors=top, fields="content_vector"
        )

        results = self.client.search(
            search_text=text_query,
            vector_queries=[vector_query],
            top=top,
        )

        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    id=result.get("id", ""),
                    title=result.get("title", "Untitled"),
                    content=result.get("content", ""),
                    source=result.get("source", "Unknown"),
                    category=result.get("category", ""),
                    file_path=result.get("file_path", ""),
                    score=result.get("@search.score", 0.0),
                    metadata={k: v for k, v in result.items() if not k.startswith("@")},
                )
            )

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
