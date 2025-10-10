"""CLI for diary management."""
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from diary_core.config import get_config
from diary_core.entry_manager import EntryManager, DiaryEntry
from diary_core.ollama_client import OllamaClient
from diary_core.template_generator import generate_prompts_for_date
from diary_core.analysis import (
    find_related_entries,
    generate_topic_tags,
    extract_todos,
    extract_themes,
    create_memory_trace_report
)
from diary_core.llm_analysis import (
    generate_semantic_backlinks,
    generate_semantic_tags
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

            ollama_client = OllamaClient(config.ollama_url, config.ollama_model)

            # Check Ollama connection
            if not ollama_client.check_connection_sync():
                console.print("[red]Error: Cannot connect to Ollama. Is it running?[/red]")
                console.print(f"Expected at: {config.ollama_url}")
                return

            prompts = generate_prompts_for_date(entry_date, entry_manager, ollama_client)

        # Get temporal links (past 3 days)
        past_dates = entry_manager.get_past_calendar_days(entry_date, 3)
        temporal_links = [d.isoformat() for d in past_dates if entry_manager.entry_exists(d)]

        # Create entry
        entry = entry_manager.create_entry_template(
            entry_date,
            prompts,
            temporal_links=temporal_links[:2] if temporal_links else None  # Limit to 2 most recent
        )

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
            console.print(f"[yellow]Entry has less than 50 characters. Skipping linking.[/yellow]")
            return

        # Initialize Ollama client
        ollama_client = OllamaClient(config.ollama_url, config.ollama_model)

        # Check Ollama connection
        if not ollama_client.check_connection_sync():
            console.print("[red]Error: Cannot connect to Ollama. Is it running?[/red]")
            console.print(f"Expected at: {config.ollama_url}")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task(description="Finding related entries with LLM...", total=None)

            # Get past entries for context
            past_entries = entry_manager.list_entries(days=90)

            # Use LLM to find semantic backlinks
            semantic_links = generate_semantic_backlinks(
                entry,
                past_entries,
                ollama_client,
                max_links=5
            )

            # Generate topic tags using LLM
            context_entries = [entry]
            tags = generate_semantic_tags(context_entries, ollama_client, max_tags=5)

        # Get temporal links (past 3 days)
        past_dates = entry_manager.get_past_calendar_days(entry_date, 3)
        temporal_links = [d.isoformat() for d in past_dates if entry_manager.entry_exists(d)]

        # Add semantic links
        for link in semantic_links:
            if link not in temporal_links:
                temporal_links.append(link)

        # Update entry
        updated_entry = entry_manager.update_memory_links(entry, temporal_links, tags)
        entry_manager.write_entry(updated_entry)

        console.print(f"[green]✓[/green] Updated links for: [bold]{entry.filename}[/bold]")
        console.print(f"[dim]  Temporal links: {len(temporal_links)}[/dim]")
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
    """Show recurring themes from recent entries."""
    try:
        config = get_config()
        entry_manager = EntryManager(config.diary_path)

        entries = entry_manager.list_entries(days=days)

        if not entries:
            console.print(f"[yellow]No entries found in past {days} days[/yellow]")
            return

        theme_list = extract_themes(entries, top_n=15)

        table = Table(title=f"Themes (past {days} days)")
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Theme", style="bold")
        table.add_column("Count", justify="right")

        for i, (theme, count) in enumerate(theme_list, 1):
            table.add_row(str(i), theme, str(count))

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
                console.print(f"[dim]Skipping {len(skipped)} entries with <50 chars:[/dim]")
                for entry in skipped[:5]:  # Show first 5
                    console.print(f"[dim]  - {entry.date.isoformat()} ({len(entry.brain_dump)} chars)[/dim]")
                if len(skipped) > 5:
                    console.print(f"[dim]  ... and {len(skipped) - 5} more[/dim]")
                console.print()

        if not entries_to_refresh:
            console.print(f"[yellow]No entries to refresh[/yellow]")
            console.print(f"[dim]Found {len(entries)} entries total, but all have <50 chars of content[/dim]")
            console.print(f"[dim]Use --all flag to refresh all entries regardless of length[/dim]")
            return

        console.print(f"[bold]Refreshing backlinks for {len(entries_to_refresh)} entries...[/bold]")
        if not all:
            console.print(f"[dim]Skipping {len(entries) - len(entries_to_refresh)} entries with <50 chars (use --all to include)[/dim]\n")
        else:
            console.print()

        # Initialize Ollama client
        ollama_client = OllamaClient(config.ollama_url, config.ollama_model)

        # Check Ollama connection
        if not ollama_client.check_connection_sync():
            console.print("[red]Error: Cannot connect to Ollama. Is it running?[/red]")
            console.print(f"Expected at: {config.ollama_url}")
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
            past_entries = entry_manager.list_entries(days=90)

            for entry in entries_to_refresh:
                # Use LLM to find semantic backlinks
                semantic_links = generate_semantic_backlinks(
                    entry,
                    past_entries,
                    ollama_client,
                    max_links=5
                )

                # Generate topic tags using LLM
                tags = generate_semantic_tags([entry], ollama_client, max_tags=5)

                # Get temporal links
                past_dates = entry_manager.get_past_calendar_days(entry.date, 3)
                temporal_links = [d.isoformat() for d in past_dates if entry_manager.entry_exists(d)]

                # Add semantic links
                for link in semantic_links:
                    if link not in temporal_links:
                        temporal_links.append(link)

                # Update entry
                updated_entry = entry_manager.update_memory_links(entry, temporal_links, tags)
                entry_manager.write_entry(updated_entry)
                updated_count += 1

                progress.update(task, advance=1)

        console.print(f"\n[green]✓[/green] Refreshed {updated_count} entries")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
