"""Diary management commands."""
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from brain_core.config import get_config, get_llm_client
from brain_core.entry_manager import EntryManager, DiaryEntry
from brain_core.template_generator import generate_prompts_for_date
from brain_core.analysis import (
    find_related_entries,
    generate_topic_tags,
    extract_todos,
    extract_themes,
    create_memory_trace_report
)
from brain_core.llm_analysis import (
    generate_semantic_backlinks,
    generate_semantic_backlinks_enhanced,
    generate_semantic_tags
)
from brain_core.constants import (
    PAST_ENTRIES_LOOKBACK_DAYS,
    MIN_SUBSTANTIAL_CONTENT_CHARS
)

app = typer.Typer(help="AI-powered diary with smart prompts and automatic backlinks")
console = Console()


def parse_date_arg(date_arg: str) -> date:
    """Parse date argument (today, yesterday, or YYYY-MM-DD)."""
    if date_arg.lower() == "today":
        return date.today()
    elif date_arg.lower() == "yesterday":
        return date.today() - timedelta(days=1)
    else:
        return date.fromisoformat(date_arg)


@app.command()
def create(
    date_arg: str = typer.Argument("today", help="Date (today, yesterday, or YYYY-MM-DD)")
):
    """Create a new diary entry with AI-generated prompts."""
    try:
        config = get_config()
        entry_date = parse_date_arg(date_arg)

        entry_manager = EntryManager(config.diary_path)

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
            if not llm_client.check_connection_sync():
                console.print(f"[red]Error: Cannot connect to LLM provider ({config.llm_provider})[/red]")
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

        entry_manager = EntryManager(config.diary_path)

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
        if not llm_client.check_connection_sync():
            console.print(f"[red]Error: Cannot connect to LLM provider ({config.llm_provider})[/red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Finding related entries with enhanced LLM analysis...", total=None)

            # Get past entries for context
            past_entries = entry_manager.list_entries(days=PAST_ENTRIES_LOOKBACK_DAYS)

            # Use enhanced LLM to find semantic backlinks with confidence scores
            semantic_links_enhanced = generate_semantic_backlinks_enhanced(
                entry,
                past_entries,
                llm_client,
                max_links=5
            )

            # Generate topic tags using LLM
            context_entries = [entry]
            tags = generate_semantic_tags(context_entries, llm_client, max_tags=5)

        # Get temporal links (past 3 days)
        past_dates = entry_manager.get_past_calendar_days(entry_date, 3)
        temporal_links = [d.isoformat() for d in past_dates if entry_manager.entry_exists(d)]

        # Build link metadata dict for enhanced display
        link_metadata = {}

        # Add semantic links with metadata
        for link in semantic_links_enhanced:
            if link.target_date not in temporal_links:
                temporal_links.append(link.target_date)
            link_metadata[link.target_date] = {
                "confidence": link.confidence,
                "reason": link.reason
            }

        # Update entry with metadata
        updated_entry = entry_manager.update_memory_links(
            entry, temporal_links, tags, link_metadata
        )
        entry_manager.write_entry(updated_entry)

        console.print(f"[green]✓[/green] Updated links for: [bold]{entry.filename}[/bold]")
        console.print(f"[dim]  Temporal links: {len(temporal_links)}[/dim]")
        console.print(f"[dim]  Semantic links: {len(semantic_links_enhanced)} (high: {sum(1 for l in semantic_links_enhanced if l.confidence == 'high')})[/dim]")
        console.print(f"[dim]  Topic tags: {len(tags)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def analyze(
    days: int = typer.Argument(30, help="Number of days to analyze")
):
    """Generate memory trace analysis report."""
    try:
        config = get_config()
        entry_manager = EntryManager(config.diary_path)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description=f"Analyzing past {days} days...", total=None)

            entries = entry_manager.list_entries(days=days)

            if not entries:
                console.print(f"[yellow]No entries found in past {days} days[/yellow]")
                return

            report = create_memory_trace_report(entries)

        console.print(report)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def todos(
    date_arg: str = typer.Argument("today", help="Date (today, yesterday, or YYYY-MM-DD)"),
    save: bool = typer.Option(False, "--save", "-s", help="Save todos to planner file")
):
    """Extract action items from an entry."""
    try:
        config = get_config()
        entry_date = parse_date_arg(date_arg)

        entry_manager = EntryManager(config.diary_path)

        entry = entry_manager.read_entry(entry_date)
        if not entry:
            console.print(f"[red]No entry found for {entry_date.isoformat()}[/red]")
            return

        todo_items = extract_todos(entry)

        if not todo_items:
            console.print(f"[yellow]No todos found in {entry_date.isoformat()}[/yellow]")
            return

        console.print(f"[bold]Todos from {entry_date.isoformat()}:[/bold]\n")
        for i, todo in enumerate(todo_items, 1):
            console.print(f"{i}. {todo}")

        if save:
            # Save to planner file
            planner_file = config.planner_path / f"{entry_date.isoformat()}-todos.md"
            content = f"# Todos from {entry_date.isoformat()}\n\n"
            for todo in todo_items:
                content += f"- [ ] {todo}\n"

            planner_file.write_text(content, encoding="utf-8")
            console.print(f"\n[green]✓[/green] Saved to: {planner_file}")

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
        entry_manager = EntryManager(config.diary_path)

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
def themes(
    days: int = typer.Argument(7, help="Number of days to analyze")
):
    """Show recurring themes from recent entries using LLM analysis."""
    try:
        config = get_config()
        entry_manager = EntryManager(config.diary_path)

        entries = entry_manager.list_entries(days=days)

        if not entries:
            console.print(f"[yellow]No entries found in past {days} days[/yellow]")
            return

        # Initialize LLM client
        llm_client = get_llm_client()

        # Check LLM connection
        if not llm_client.check_connection_sync():
            console.print(f"[red]Error: Cannot connect to LLM provider ({config.llm_provider})[/red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Analyzing themes with LLM...", total=None)

            # Use LLM to extract semantic themes (request more tags for themes view)
            theme_list = generate_semantic_tags(entries, llm_client, max_tags=15)

        if not theme_list:
            console.print(f"[yellow]No themes identified in past {days} days[/yellow]")
            return

        table = Table(title=f"Themes (past {days} days)")
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Theme", style="bold")

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
        entry_manager = EntryManager(config.diary_path)

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
            console.print(f"[yellow]No entries to refresh[/yellow]")
            console.print(f"[dim]Found {len(entries)} entries total, but all have <{MIN_SUBSTANTIAL_CONTENT_CHARS} chars of content[/dim]")
            console.print(f"[dim]Use --all flag to refresh all entries regardless of length[/dim]")
            return

        console.print(f"[bold]Refreshing backlinks for {len(entries_to_refresh)} entries...[/bold]")
        if not all:
            console.print(f"[dim]Skipping {len(entries) - len(entries_to_refresh)} entries with <{MIN_SUBSTANTIAL_CONTENT_CHARS} chars (use --all to include)[/dim]\n")
        else:
            console.print()

        # Initialize LLM client
        llm_client = get_llm_client()

        # Check LLM connection
        if not llm_client.check_connection_sync():
            console.print(f"[red]Error: Cannot connect to LLM provider ({config.llm_provider})[/red]")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                description=f"Processing entries with LLM...",
                total=len(entries_to_refresh)
            )

            updated_count = 0
            past_entries = entry_manager.list_entries(days=PAST_ENTRIES_LOOKBACK_DAYS)

            for entry in entries_to_refresh:
                # Use enhanced LLM to find semantic backlinks
                semantic_links_enhanced = generate_semantic_backlinks_enhanced(
                    entry,
                    past_entries,
                    llm_client,
                    max_links=5
                )

                # Generate topic tags using LLM
                tags = generate_semantic_tags([entry], llm_client, max_tags=5)

                # Get temporal links
                past_dates = entry_manager.get_past_calendar_days(entry.date, 3)
                temporal_links = [d.isoformat() for d in past_dates if entry_manager.entry_exists(d)]

                # Build link metadata
                link_metadata = {}
                for link in semantic_links_enhanced:
                    if link.target_date not in temporal_links:
                        temporal_links.append(link.target_date)
                    link_metadata[link.target_date] = {
                        "confidence": link.confidence,
                        "reason": link.reason
                    }

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
