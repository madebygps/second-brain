"""Main CLI entry point for the brain system."""
import logging
import sys
import typer

# Import subcommands
from brain_cli.diary_commands import app as diary_app
from brain_cli.notes_commands import app as notes_app
from brain_cli.plan_commands import app as plan_app

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Only show warnings and errors by default
    format='%(levelname)s: %(message)s',
    stream=sys.stderr
)

app = typer.Typer(
    help="Your AI-powered second brain for journaling with semantic backlinks and intelligent notes search",
    no_args_is_help=True,
    add_completion=False
)

# Register subcommands
app.add_typer(diary_app, name="diary")
app.add_typer(notes_app, name="notes")
app.add_typer(plan_app, name="plan")


if __name__ == "__main__":
    app()
