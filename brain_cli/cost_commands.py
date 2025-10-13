"""Cost tracking and analysis commands."""

from datetime import date, timedelta

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from brain_core.cost_tracker import get_cost_tracker

app = typer.Typer(
    help="Track and analyze Azure OpenAI costs", no_args_is_help=True, add_completion=False
)

console = Console()


@app.command()
def summary(
    days: int | None = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
    month: str | None = typer.Option(None, "--month", "-m", help="Specific month (YYYY-MM format)"),
) -> None:
    """Show cost summary for a time period."""
    cost_tracker = get_cost_tracker()

    try:
        if month:
            # Parse month format YYYY-MM
            year, month_num = map(int, month.split("-"))
            summary = cost_tracker.get_monthly_summary(year, month_num)
            period_desc = f"{year}-{month_num:02d}"
        else:
            summary = cost_tracker.get_summary(days=days)
            period_desc = f"Last {days} days"

        if summary.total_requests == 0:
            console.print(f"[yellow]No usage data found for {period_desc}[/yellow]")
            return

        # Main summary panel
        summary_text = Text()
        summary_text.append("Total Cost: ", style="bold")
        summary_text.append(f"${summary.total_cost:.2f}\n", style="bold green")
        summary_text.append(f"Total Tokens: {summary.total_tokens:,}\n")
        summary_text.append(f"Total Requests: {summary.total_requests}\n")

        # Calculate averages
        if not month:
            period_days = days or 30
        else:
            period_days = (date.today() - date(year, month_num, 1)).days + 1

        if period_days > 0 and summary.by_day:
            avg_cost_per_day = summary.total_cost / min(period_days, len(summary.by_day))
            summary_text.append(f"Average per day: ${avg_cost_per_day:.2f}\n")

        console.print(
            Panel(
                summary_text, title=f"Brain Tool Cost Summary ({period_desc})", border_style="blue"
            )
        )

        # By operation table
        if summary.by_operation:
            operation_table = Table(title="Cost by Operation", box=box.ROUNDED)
            operation_table.add_column("Operation", style="cyan")
            operation_table.add_column("Cost", style="green", justify="right")
            operation_table.add_column("Tokens", justify="right")
            operation_table.add_column("Requests", justify="right")
            operation_table.add_column("Avg Cost/Request", style="yellow", justify="right")

            # Sort by cost descending
            sorted_ops = sorted(
                summary.by_operation.items(), key=lambda x: x[1]["cost"], reverse=True
            )

            for operation, data in sorted_ops:
                avg_cost = data["cost"] / data["requests"] if data["requests"] > 0 else 0
                operation_table.add_row(
                    operation.title().replace("_", " "),
                    f"${data['cost']:.2f}",
                    f"{data['tokens']:,}",
                    str(data["requests"]),
                    f"${avg_cost:.4f}",
                )

            console.print(operation_table)

        # Recent daily activity (last 7 days)
        if summary.by_day:
            daily_table = Table(title="Recent Daily Activity", box=box.ROUNDED)
            daily_table.add_column("Date", style="cyan")
            daily_table.add_column("Cost", style="green", justify="right")
            daily_table.add_column("Tokens", justify="right")
            daily_table.add_column("Requests", justify="right")

            # Show last 7 days with data
            sorted_days = sorted(summary.by_day.items(), reverse=True)[:7]

            for day, data in sorted_days:
                daily_table.add_row(
                    day, f"${data['cost']:.2f}", f"{data['tokens']:,}", str(data["requests"])
                )

            console.print(daily_table)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Month format should be YYYY-MM (e.g., 2025-10)[/yellow]")


@app.command()
def trends(
    days: int = typer.Option(14, "--days", "-d", help="Number of days to show trends for"),
) -> None:
    """Show daily cost trends."""
    cost_tracker = get_cost_tracker()

    trends_data = cost_tracker.get_trends(days=days)

    if not any(cost > 0 for _, cost in trends_data):
        console.print(f"[yellow]No usage data found for the last {days} days[/yellow]")
        return

    # Create trends table
    trends_table = Table(title=f"Daily Cost Trends (Last {days} Days)", box=box.ROUNDED)
    trends_table.add_column("Date", style="cyan")
    trends_table.add_column("Cost", style="green", justify="right")
    trends_table.add_column("Trend", justify="center")

    max_cost = max(cost for _, cost in trends_data)

    for i, (day, cost) in enumerate(trends_data):
        # Simple trend indicator
        trend_indicator = ""
        if i > 0:
            prev_cost = trends_data[i - 1][1]
            if cost > prev_cost:
                trend_indicator = "📈"
            elif cost < prev_cost:
                trend_indicator = "📉"
            else:
                trend_indicator = "➡️"

        # Visual bar (simple ASCII)
        if max_cost > 0:
            bar_length = int((cost / max_cost) * 20)
            bar = "█" * bar_length
        else:
            bar = ""

        trends_table.add_row(day, f"${cost:.2f}", f"{trend_indicator} {bar}")

    console.print(trends_table)


@app.command()
def estimate(
    sample_days: int = typer.Option(7, "--sample-days", "-s", help="Days to base estimate on"),
) -> None:
    """Estimate monthly costs based on recent usage."""
    cost_tracker = get_cost_tracker()

    monthly_estimate = cost_tracker.estimate_monthly_cost(days_sample=sample_days)
    recent_summary = cost_tracker.get_summary(days=sample_days)

    if recent_summary.total_requests == 0:
        console.print(f"[yellow]No usage data found for the last {sample_days} days[/yellow]")
        return

    # Estimate panel
    estimate_text = Text()
    estimate_text.append("Estimated Monthly Cost: ", style="bold")
    estimate_text.append(f"${monthly_estimate:.2f}\n", style="bold green")
    estimate_text.append(f"Based on last {sample_days} days of usage\n", style="dim")
    estimate_text.append(f"Recent daily average: ${recent_summary.total_cost / sample_days:.2f}\n")

    # Confidence indicator
    if recent_summary.total_requests >= 10:
        confidence = "High"
        confidence_color = "green"
    elif recent_summary.total_requests >= 5:
        confidence = "Medium"
        confidence_color = "yellow"
    else:
        confidence = "Low"
        confidence_color = "red"

    estimate_text.append("Confidence: ", style="bold")
    estimate_text.append(f"{confidence}", style=f"bold {confidence_color}")
    estimate_text.append(f" ({recent_summary.total_requests} recent requests)")

    console.print(Panel(estimate_text, title="Monthly Cost Estimate", border_style="blue"))


@app.command()
def breakdown(
    days: int = typer.Option(30, "--days", "-d", help="Number of days to analyze"),
) -> None:
    """Show detailed cost breakdown by operation type."""
    cost_tracker = get_cost_tracker()
    summary = cost_tracker.get_summary(days=days)

    if summary.total_requests == 0:
        console.print(f"[yellow]No usage data found for the last {days} days[/yellow]")
        return

    console.print(f"\n[bold blue]Detailed Cost Breakdown (Last {days} Days)[/bold blue]\n")

    # Sort operations by cost
    sorted_ops = sorted(summary.by_operation.items(), key=lambda x: x[1]["cost"], reverse=True)

    for operation, data in sorted_ops:
        cost = data["cost"]
        tokens = data["tokens"]
        requests = data["requests"]

        # Calculate percentages
        cost_pct = (cost / summary.total_cost) * 100 if summary.total_cost > 0 else 0
        token_pct = (tokens / summary.total_tokens) * 100 if summary.total_tokens > 0 else 0

        # Create operation panel
        op_text = Text()
        op_text.append(f"Cost: ${cost:.2f} ({cost_pct:.1f}% of total)\n")
        op_text.append(f"Tokens: {tokens:,} ({token_pct:.1f}% of total)\n")
        op_text.append(f"Requests: {requests}\n")
        op_text.append(f"Avg per request: ${cost/requests:.4f}")

        console.print(
            Panel(op_text, title=operation.title().replace("_", " "), border_style="cyan")
        )


@app.command()
def export(
    output_file: str = typer.Argument(..., help="Output file path (JSON format)"),
    days: int | None = typer.Option(None, "--days", "-d", help="Number of days to export"),
    month: str | None = typer.Option(None, "--month", "-m", help="Specific month (YYYY-MM)"),
) -> None:
    """Export usage data to JSON file."""
    import json
    from pathlib import Path

    cost_tracker = get_cost_tracker()

    try:
        if month:
            year, month_num = map(int, month.split("-"))
            start_date = date(year, month_num, 1)
            if month_num == 12:
                end_date = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(year, month_num + 1, 1) - timedelta(days=1)
        elif days:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
        else:
            # Default to last 90 days
            end_date = date.today()
            start_date = end_date - timedelta(days=90)

        data = cost_tracker.export_data(start_date=start_date, end_date=end_date)

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        console.print(f"[green]Exported {len(data)} records to {output_path}[/green]")

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Month format should be YYYY-MM (e.g., 2025-10)[/yellow]")
    except Exception as e:
        console.print(f"[red]Export failed: {e}[/red]")


@app.command()
def pricing(
    model: str | None = typer.Option(None, "--model", "-m", help="Show pricing for specific model"),
    update: bool = typer.Option(False, "--update", help="Update pricing from current rates"),
) -> None:
    """Show or update current pricing information."""
    cost_tracker = get_cost_tracker()

    if update:
        console.print(
            "[yellow]Pricing updates not yet implemented. Please update manually in cost_tracker.py[/yellow]"
        )
        return

    pricing_table = Table(title="Current Azure OpenAI Pricing", box=box.ROUNDED)
    pricing_table.add_column("Model", style="cyan")
    pricing_table.add_column("Input (per 1K tokens)", style="green", justify="right")
    pricing_table.add_column("Output (per 1K tokens)", style="yellow", justify="right")

    pricing_data = cost_tracker.PRICING

    if model:
        model_key = model.lower()
        if model_key in pricing_data:
            pricing_data = {model_key: pricing_data[model_key]}
        else:
            console.print(f"[red]Model '{model}' not found in pricing data[/red]")
            return

    for model_name, prices in pricing_data.items():
        pricing_table.add_row(
            model_name, f"${prices['input'] * 1000:.6f}", f"${prices['output'] * 1000:.6f}"
        )

    console.print(pricing_table)
    console.print(
        "\n[dim]Note: Prices are estimates based on Azure OpenAI pricing as of October 2025[/dim]"
    )
    console.print("[dim]Use --update flag to refresh rates (feature coming soon)[/dim]")


if __name__ == "__main__":
    app()
