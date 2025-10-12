"""Notes management and search commands."""
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional

from brain_core.azure_search_client import get_azure_search_client

app = typer.Typer(help="Search and manage book notes using Azure AI Search")
console = Console()


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query (e.g., 'notes on discipline')"),
    top: int = typer.Option(10, "--top", "-n", help="Maximum number of results to return"),
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

        if not search_client:
            console.print("[red]Error: Azure Search is not configured[/red]")
            console.print("\n[yellow]Please set the following environment variables in your .env file:[/yellow]")
            console.print("  - AZURE_SEARCH_ENDPOINT")
            console.print("  - AZURE_SEARCH_API_KEY")
            console.print("  - AZURE_SEARCH_INDEX_NAME (optional, defaults to 'notes-index')")
            raise typer.Exit(1)

        # Check connection
        if not search_client.check_connection():
            console.print("[red]Error: Cannot connect to Azure Search service[/red]")
            console.print(f"[dim]Endpoint: {search_client.endpoint}[/dim]")
            console.print(f"[dim]Index: {search_client.index_name}[/dim]")
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
            table.add_column("#", style="dim", width=3, justify="right")
            table.add_column("Book", style="bold")
            table.add_column("Category", style="yellow", width=12)
            table.add_column("Words", justify="right", width=7)
            table.add_column("Score", justify="right", width=7)
            table.add_column("Preview", style="dim")

            for i, result in enumerate(results, 1):
                # Create preview (first 80 chars)
                preview = result.content[:80].replace("\n", " ")
                if len(result.content) > 80:
                    preview += "..."

                table.add_row(
                    str(i),
                    result.title,
                    result.category,
                    str(result.word_count),
                    f"{result.score:.2f}",
                    preview
                )

            console.print(table)
            console.print(f"\n[dim]Use --detailed flag to see full content[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """Check Azure Search connection status and configuration."""
    try:
        search_client = get_azure_search_client()

        if not search_client:
            console.print("[yellow]Azure Search is not configured[/yellow]\n")
            console.print("Required environment variables:")
            console.print("  - AZURE_SEARCH_ENDPOINT")
            console.print("  - AZURE_SEARCH_API_KEY")
            console.print("  - AZURE_SEARCH_INDEX_NAME (optional)")
            raise typer.Exit(1)

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
