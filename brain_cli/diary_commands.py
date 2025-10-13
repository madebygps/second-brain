"""Diary management commands."""
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import date, timedelta

from brain_core.config import get_config, get_llm_client
from brain_core.entry_manager import EntryManager
from brain_core.template_generator import generate_prompts_for_date
from brain_core.report_generator import create_memory_trace_report
from brain_core.llm_analysis import (
    generate_semantic_backlinks,
    generate_semantic_tags
)
from brain_core.constants import (
    PAST_ENTRIES_LOOKBACK_DAYS,
    MIN_SUBSTANTIAL_CONTENT_CHARS
)

app = typer.Typer(help="AI-powered diary with smart prompts and automatic backlinks")
console = Console()

# Constants
TEMPORAL_LOOKBACK_DAYS = 3
MAX_SEMANTIC_LINKS = 5
MAX_TOPIC_TAGS = 5
MAX_PATTERN_TAGS = 15


def parse_date_arg(date_arg: str) -> date:
    """Parse date argument (today, yesterday, or YYYY-MM-DD).
    
    Args:
        date_arg: Date string to parse ("today", "yesterday", or "YYYY-MM-DD")
        
    Returns:
        Parsed date object
    """
    if date_arg.lower() == "today":
        return date.today()
    elif date_arg.lower() == "yesterday":
        return date.today() - timedelta(days=1)
    else:
        return date.fromisoformat(date_arg)


def check_llm_connection(llm_client) -> bool:
    """Check LLM connection and print error if unavailable.
    
    Args:
        llm_client: LLM client instance to check
        
    Returns:
        True if connection successful, False otherwise
    """
    if not llm_client.check_connection_sync():
        console.print("[red]Error: Cannot connect to Azure OpenAI[/red]")
        return False
    return True


def generate_entry_links(entry, entry_manager, llm_client):
    """Generate semantic and temporal links for an entry.
    
    Args:
        entry: DiaryEntry to generate links for
        entry_manager: EntryManager instance
        llm_client: LLM client for semantic analysis
        
    Returns:
        Tuple of (temporal_links, tags, link_metadata, semantic_links)
    """
    # Get past entries for semantic analysis
    past_entries = entry_manager.list_entries(days=PAST_ENTRIES_LOOKBACK_DAYS)
    
    # Use LLM to find semantic backlinks with confidence scores
    semantic_links = generate_semantic_backlinks(
        entry,
        past_entries,
        llm_client,
        max_links=MAX_SEMANTIC_LINKS
    )
    
    # Generate topic tags using LLM
    tags = generate_semantic_tags([entry], llm_client, max_tags=MAX_TOPIC_TAGS)
    
    # Get temporal links (past N days)
    past_dates = entry_manager.get_past_calendar_days(entry.date, TEMPORAL_LOOKBACK_DAYS)
    temporal_links = [d.isoformat() for d in past_dates if entry_manager.entry_exists(d)]
    
    # Build link metadata dict for enhanced display
    link_metadata = {}
    for link in semantic_links:
        if link.target_date not in temporal_links:
            temporal_links.append(link.target_date)
        link_metadata[link.target_date] = {
            "confidence": link.confidence,
            "reason": link.reason
        }
    
    return temporal_links, tags, link_metadata, semantic_links


@app.command()
def create(
    date_arg: str = typer.Argument("today", help="Date (today, yesterday, or YYYY-MM-DD)")
):
    """Create a new diary entry with AI-generated prompts."""
    try:
        config = get_config()
        entry_date = parse_date_arg(date_arg)

        entry_manager = EntryManager(config.diary_path, config.planner_path)

        # Check if entry already exists
        if entry_manager.entry_exists(entry_date):
            console.print(f"[yellow]Entry for {entry_date.isoformat()} already exists[/yellow]")
            return

        # Generate prompts with progress indicator
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Generating AI prompts...", total=None)

            llm_client = get_llm_client()

            # Check LLM connection
            if not check_llm_connection(llm_client):
                return

            prompts = generate_prompts_for_date(entry_date, entry_manager, llm_client)

        # Create entry (no memory links yet - those are added with 'diary link')
        entry = entry_manager.create_entry_template(entry_date, prompts)

        entry_manager.write_entry(entry)

        console.print(f"[green]✓[/green] Created entry: [bold]{entry.filename}[/bold]")
        console.print(f"[dim]Location: {config.diary_path / entry.filename}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def link(
    date_arg: str = typer.Argument("today", help="Date (today, yesterday, or YYYY-MM-DD)")
):
    """Generate backlinks and tags for an existing entry."""
    try:
        config = get_config()
        entry_date = parse_date_arg(date_arg)

        entry_manager = EntryManager(config.diary_path, config.planner_path)

        # Check if entry exists
        entry = entry_manager.read_entry(entry_date)
        if not entry:
            console.print(f"[red]No entry found for {entry_date.isoformat()}[/red]")
            return

        # Check if entry has substantial content
        if not entry.has_substantial_content:
            console.print(f"[yellow]Entry has less than {MIN_SUBSTANTIAL_CONTENT_CHARS} characters. Skipping linking.[/yellow]")
            return

        # Initialize LLM client
        llm_client = get_llm_client()

        # Check LLM connection
        if not check_llm_connection(llm_client):
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Finding related entries with enhanced LLM analysis...", total=None)

            # Generate all links using helper function
            temporal_links, tags, link_metadata, semantic_links = generate_entry_links(
                entry, entry_manager, llm_client
            )

        # Update entry with metadata
        updated_entry = entry_manager.update_memory_links(
            entry, temporal_links, tags, link_metadata
        )
        entry_manager.write_entry(updated_entry)

        console.print(f"[green]✓[/green] Updated links for: [bold]{entry.filename}[/bold]")
        console.print(f"[dim]  Temporal links: {len(temporal_links)}[/dim]")
        console.print(f"[dim]  Semantic links: {len(semantic_links)} (high: {sum(1 for link in semantic_links if link.confidence == 'high')})[/dim]")
        console.print(f"[dim]  Topic tags: {len(tags)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def report(
    days: int = typer.Argument(30, help="Number of days to include in report")
):
    """Generate a memory trace report showing recurring activities and semantic connections between entries."""
    try:
        config = get_config()
        llm_client = get_llm_client()
        entry_manager = EntryManager(config.diary_path, config.planner_path)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description=f"Generating memory trace report for past {days} days...", total=None)

            entries = entry_manager.list_entries(days=days)

            if not entries:
                console.print(f"[yellow]No entries found in past {days} days[/yellow]")
                return

            report = create_memory_trace_report(entries, llm_client)

        console.print(report)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def list(
    days: int = typer.Argument(7, help="Number of days to list")
):
    """List recent diary entries."""
    try:
        config = get_config()
        entry_manager = EntryManager(config.diary_path, config.planner_path)

        entries = entry_manager.list_entries(days=days)

        if not entries:
            console.print(f"[yellow]No entries found in past {days} days[/yellow]")
            return

        table = Table(title=f"Recent Entries (past {days} days)")
        table.add_column("Date", style="cyan")
        table.add_column("Preview", style="white")
        table.add_column("Length", justify="right")

        for entry in entries:
            preview = entry.brain_dump[:60].replace("\n", " ")
            if len(entry.brain_dump) > 60:
                preview += "..."

            table.add_row(
                entry.date.isoformat(),
                preview,
                str(len(entry.brain_dump))
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def patterns(
    days: int = typer.Argument(7, help="Number of days to analyze")
):
    """Identify emotional and psychological patterns from recent entries using LLM analysis."""
    try:
        config = get_config()
        entry_manager = EntryManager(config.diary_path, config.planner_path)

        entries = entry_manager.list_entries(days=days)

        if not entries:
            console.print(f"[yellow]No entries found in past {days} days[/yellow]")
            return

        # Initialize LLM client
        llm_client = get_llm_client()

        # Check LLM connection
        if not check_llm_connection(llm_client):
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Analyzing emotional patterns with LLM...", total=None)

            # Use LLM to extract semantic themes (request more tags for patterns view)
            theme_list = generate_semantic_tags(entries, llm_client, max_tags=MAX_PATTERN_TAGS)

        if not theme_list:
            console.print(f"[yellow]No patterns identified in past {days} days[/yellow]")
            return

        table = Table(title=f"Emotional & Psychological Patterns (past {days} days)")
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Pattern", style="bold")

        for i, theme in enumerate(theme_list, 1):
            table.add_row(str(i), f"#{theme}")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def refresh(
    days: int = typer.Argument(30, help="Number of days to refresh backlinks for"),
    all: bool = typer.Option(False, "--all", "-a", help="Include entries with <50 chars"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show skipped entries")
):
    """Refresh backlinks and tags for all entries in the past N days."""
    try:
        config = get_config()
        entry_manager = EntryManager(config.diary_path, config.planner_path)

        entries = entry_manager.list_entries(days=days)

        if not entries:
            console.print(f"[yellow]No entries found in past {days} days[/yellow]")
            return

        # Filter to entries with substantial content (unless --all flag is used)
        if all:
            entries_to_refresh = entries
        else:
            entries_to_refresh = [e for e in entries if e.has_substantial_content]
            skipped = [e for e in entries if not e.has_substantial_content]

            if verbose and skipped:
                console.print(f"[dim]Skipping {len(skipped)} entries with <{MIN_SUBSTANTIAL_CONTENT_CHARS} chars:[/dim]")
                for entry in skipped[:5]:  # Show first 5
                    console.print(f"[dim]  - {entry.date.isoformat()} ({len(entry.brain_dump)} chars)[/dim]")
                if len(skipped) > 5:
                    console.print(f"[dim]  ... and {len(skipped) - 5} more[/dim]")
                console.print()

        if not entries_to_refresh:
            console.print("[yellow]No entries to refresh[/yellow]")
            console.print(f"[dim]Found {len(entries)} entries total, but all have <{MIN_SUBSTANTIAL_CONTENT_CHARS} chars of content[/dim]")
            console.print("[dim]Use --all flag to refresh all entries regardless of length[/dim]")
            return

        console.print(f"[bold]Refreshing backlinks for {len(entries_to_refresh)} entries...[/bold]")
        if not all:
            console.print(f"[dim]Skipping {len(entries) - len(entries_to_refresh)} entries with <{MIN_SUBSTANTIAL_CONTENT_CHARS} chars (use --all to include)[/dim]\n")
        else:
            console.print()

        # Initialize LLM client
        llm_client = get_llm_client()

        # Check LLM connection
        if not check_llm_connection(llm_client):
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                description="Processing entries with LLM...",
                total=len(entries_to_refresh)
            )

            updated_count = 0

            for entry in entries_to_refresh:
                # Generate all links using helper function
                temporal_links, tags, link_metadata, _ = generate_entry_links(
                    entry, entry_manager, llm_client
                )

                # Update entry with metadata
                updated_entry = entry_manager.update_memory_links(
                    entry, temporal_links, tags, link_metadata
                )
                entry_manager.write_entry(updated_entry)
                updated_count += 1

                progress.update(task, advance=1)

        console.print(f"\n[green]✓[/green] Refreshed {updated_count} entries")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
