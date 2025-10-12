"""Main CLI entry point for the brain system."""
import typer
from rich.console import Console

# Import subcommands
from brain_cli import diary_commands, daemon_commands, notes_commands

app = typer.Typer(
    help="Your AI-powered second brain - unified interface for diary, notes, and planning",
    no_args_is_help=True
)
console = Console()

# Register subcommands
app.add_typer(diary_commands.app, name="diary", help="Diary management with AI prompts and backlinks")
app.add_typer(daemon_commands.app, name="daemon", help="Background automation daemon")
app.add_typer(notes_commands.app, name="notes", help="Search book notes using Azure AI Search")

# Future subcommands can be added here:
# app.add_typer(planner_commands.app, name="planner", help="Task planning and tracking")


if __name__ == "__main__":
    app()
