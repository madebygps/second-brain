"""Notes management and search commands."""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from brain_core.config import get_azure_search_client

app = typer.Typer(help="Search and manage book notes using Azure AI Search")
console = Console()

# Constants
DEFAULT_TOP_RESULTS = 10
PREVIEW_LENGTH = 80
TABLE_COL_WIDTH_INDEX = 3
TABLE_COL_WIDTH_CATEGORY = 12
TABLE_COL_WIDTH_WORDS = 7
TABLE_COL_WIDTH_SCORE = 7


def check_search_connection(search_client) -> bool:
    """Check Azure Search connection and display error if unavailable.
    
    Args:
        search_client: Azure Search client instance to check
        
    Returns:
        True if connection successful, False otherwise
    """
    if not search_client.check_connection():
        console.print("[red]Error: Cannot connect to Azure Search service[/red]")
        console.print(f"[dim]Endpoint: {search_client.endpoint}[/dim]")
        console.print(f"[dim]Index: {search_client.index_name}[/dim]")
        return False
    return True


def create_result_preview(content: str, max_length: int = PREVIEW_LENGTH) -> str:
    """Create a preview string from content.
    
    Args:
        content: Full content text
        max_length: Maximum length of preview
        
    Returns:
        Truncated preview string with ellipsis if needed
    """
    preview = content[:max_length].replace("\n", " ")
    if len(content) > max_length:
        preview += "..."
    return preview


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (e.g., 'notes on discipline')"),
    top: int = typer.Option(DEFAULT_TOP_RESULTS, "--top", "-n", help="Maximum number of results to return"),
    semantic: bool = typer.Option(False, "--semantic", "-s", help="Use semantic search (slower but more relevant)"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show full content of results")
):
    """Search book notes using Azure AI Search.

    Examples:
        brain notes search "discipline and habits"
        brain notes search "productivity tips" --top 5
        brain notes search "notes on learning" --semantic
        brain notes search "deep work" --detailed
    """
    try:
        # Get Azure Search client
        search_client = get_azure_search_client()

        # Check connection
        if not check_search_connection(search_client):
            raise typer.Exit(1)

        # Perform search
        with console.status(f"[bold cyan]Searching for '{query}'...", spinner="dots"):
            if semantic:
                results = search_client.semantic_search(query, top=top)
                search_type = "Semantic"
            else:
                results = search_client.search(query, top=top)
                search_type = "Text"

        if not results:
            console.print(f"\n[yellow]No results found for '{query}'[/yellow]")
            return

        # Display results
        console.print(f"\n[bold cyan]{search_type} Search Results[/bold cyan] for: [bold]'{query}'[/bold]")
        console.print(f"[dim]Found {len(results)} result(s)[/dim]\n")

        if detailed:
            # Detailed view - show full content
            for i, result in enumerate(results, 1):
                # Create panel with result
                panel_content = f"**Book:** {result.title}\n"
                panel_content += f"**Category:** {result.category}\n"
                panel_content += f"**Source:** {result.source}\n"
                panel_content += f"**Score:** {result.score:.2f} | **Words:** {result.word_count}\n\n"
                panel_content += "---\n\n"
                panel_content += result.content

                panel = Panel(
                    Markdown(panel_content),
                    title=f"[bold cyan]{i}. Note from {result.title}[/bold cyan]",
                    border_style="cyan",
                    expand=False
                )
                console.print(panel)
                console.print()  # Add spacing between results
        else:
            # Table view - compact overview
            table = Table(show_header=True, header_style="bold cyan", expand=True)
            table.add_column("#", style="dim", width=TABLE_COL_WIDTH_INDEX, justify="right")
            table.add_column("Book", style="bold")
            table.add_column("Category", style="yellow", width=TABLE_COL_WIDTH_CATEGORY)
            table.add_column("Words", justify="right", width=TABLE_COL_WIDTH_WORDS)
            table.add_column("Score", justify="right", width=TABLE_COL_WIDTH_SCORE)
            table.add_column("Preview", style="dim")

            for i, result in enumerate(results, 1):
                preview = create_result_preview(result.content)

                table.add_row(
                    str(i),
                    result.title,
                    result.category,
                    str(result.word_count),
                    f"{result.score:.2f}",
                    preview
                )

            console.print(table)
            console.print("\n[dim]Use --detailed flag to see full content[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Check Azure Search connection status and configuration."""
    try:
        search_client = get_azure_search_client()

        console.print("[bold]Azure Search Configuration[/bold]\n")
        console.print(f"Endpoint: [cyan]{search_client.endpoint}[/cyan]")
        console.print(f"Index: [cyan]{search_client.index_name}[/cyan]\n")

        with console.status("Testing connection...", spinner="dots"):
            connected = search_client.check_connection()

        if connected:
            console.print("[green]✓[/green] Connection successful!")
        else:
            console.print("[red]✗[/red] Connection failed")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
