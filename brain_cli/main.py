"""Main CLI entry point for the brain system."""

from importlib.metadata import PackageNotFoundError, version

import typer

from brain_cli.cost_commands import app as cost_app

# Import subcommands
from brain_cli.diary_commands import app as diary_app
from brain_cli.plan_commands import app as plan_app

# Import centralized logging
from brain_core.logging_config import setup_logging


def version_callback(value: bool):
    """Show version information."""
    if value:
        try:
            pkg_version = version("second-brain")
        except PackageNotFoundError:
            pkg_version = "0.1.0 (dev)"
        typer.echo(f"Brain CLI v{pkg_version}")
        raise typer.Exit()


def main_callback(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose (INFO) logging"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug logging"),
    version: bool | None = typer.Option(
        None, "--version", callback=version_callback, help="Show version"
    ),
    log_format: str = typer.Option(
        "simple", "--log-format", help="Logging format (simple, detailed, json)"
    ),
    disable_file_logging: bool = typer.Option(False, "--no-file-logs", help="Disable file logging"),
) -> None:
    """Main callback to set up logging before running commands."""
    # Determine log level
    if debug:
        log_level = "DEBUG"
    elif verbose:
        log_level = "INFO"
    else:
        log_level = "WARNING"

    # Setup centralized logging
    setup_logging(
        level=log_level, console_format=log_format, enable_file_logging=not disable_file_logging
    )


app = typer.Typer(
    help="Your AI-powered second brain for journaling and planning with semantic backlinks",
    no_args_is_help=True,
    add_completion=False,
    callback=main_callback,
)

# Register subcommands
app.add_typer(diary_app, name="diary")
app.add_typer(plan_app, name="plan")
app.add_typer(cost_app, name="cost")


if __name__ == "__main__":
    app()
