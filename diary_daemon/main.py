"""Daemon management CLI."""
import typer
import subprocess
import signal
import sys
from pathlib import Path
from rich.console import Console

app = typer.Typer(help="Manage diary background daemon")
console = Console()

PIDFILE = Path.home() / ".diary-daemon.pid"


@app.command()
def start():
    """Start the diary daemon in the background."""
    # Check if already running
    if PIDFILE.exists():
        pid = int(PIDFILE.read_text())
        try:
            # Check if process is still running
            import os
            os.kill(pid, 0)
            console.print(f"[yellow]Daemon already running (PID: {pid})[/yellow]")
            return
        except OSError:
            # Process not running, remove stale pidfile
            PIDFILE.unlink()

    # Start daemon in background
    daemon_script = Path(__file__).parent / "scheduler.py"

    # Run daemon as background process
    process = subprocess.Popen(
        [sys.executable, str(daemon_script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )

    # Save PID
    PIDFILE.write_text(str(process.pid))

    console.print(f"[green]✓[/green] Daemon started (PID: {process.pid})")
    console.print("[dim]Use 'diary-daemon stop' to stop it[/dim]")


@app.command()
def stop():
    """Stop the diary daemon."""
    if not PIDFILE.exists():
        console.print("[yellow]Daemon is not running[/yellow]")
        return

    pid = int(PIDFILE.read_text())

    try:
        # Send SIGTERM for graceful shutdown
        import os
        os.kill(pid, signal.SIGTERM)

        # Wait a bit for graceful shutdown
        import time
        time.sleep(1)

        # Check if still running
        try:
            os.kill(pid, 0)
            # Still running, force kill
            console.print("[yellow]Daemon didn't stop gracefully, forcing...[/yellow]")
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

        PIDFILE.unlink()
        console.print(f"[green]✓[/green] Daemon stopped (PID: {pid})")

    except OSError:
        console.print(f"[yellow]Daemon (PID: {pid}) was not running[/yellow]")
        PIDFILE.unlink()


@app.command()
def status():
    """Check daemon status."""
    if not PIDFILE.exists():
        console.print("[yellow]Daemon is not running[/yellow]")
        return

    pid = int(PIDFILE.read_text())

    try:
        import os
        os.kill(pid, 0)
        console.print(f"[green]✓[/green] Daemon is running (PID: {pid})")
    except OSError:
        console.print(f"[red]Daemon (PID: {pid}) is not running (stale pidfile)[/red]")
        PIDFILE.unlink()


if __name__ == "__main__":
    app()
