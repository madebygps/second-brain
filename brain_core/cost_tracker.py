"""Cost tracking system for Azure OpenAI usage."""

import json
import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)


@dataclass
class LLMUsage:
    """Represents a single LLM API call usage record."""

    timestamp: datetime
    operation: str  # backlinks, tags, reports, task_extraction, etc.
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    elapsed_seconds: float
    estimated_cost: float
    entry_date: str | None = None  # For operations tied to specific entries
    metadata: dict | None = None  # Additional context


class CostSummary(NamedTuple):
    """Summary of costs for a time period."""

    total_cost: float
    total_tokens: int
    total_requests: int
    by_operation: dict[str, dict[str, float]]  # operation -> {cost, tokens, requests}
    by_day: dict[str, dict[str, float]]  # date -> {cost, tokens, requests}


class CostTracker:
    """Tracks and analyzes Azure OpenAI usage costs."""

    @staticmethod
    def _get_pricing() -> dict[str, dict[str, float]]:
        """Get pricing configuration from environment variables or defaults.

        Environment variables can override pricing:
        - AZURE_GPT4O_INPUT_PRICE: Price per 1K input tokens for gpt-4o
        - AZURE_GPT4O_OUTPUT_PRICE: Price per 1K output tokens for gpt-4o
        - AZURE_GPT4O_MINI_INPUT_PRICE: Price per 1K input tokens for gpt-4o-mini
        - AZURE_GPT4O_MINI_OUTPUT_PRICE: Price per 1K output tokens for gpt-4o-mini
        """
        return {
            "gpt-4o": {
                "input": float(os.getenv("AZURE_GPT4O_INPUT_PRICE", "0.03")) / 1000,
                "output": float(os.getenv("AZURE_GPT4O_OUTPUT_PRICE", "0.06")) / 1000,
            },
            "gpt-4o-mini": {
                "input": float(os.getenv("AZURE_GPT4O_MINI_INPUT_PRICE", "0.0015")) / 1000,
                "output": float(os.getenv("AZURE_GPT4O_MINI_OUTPUT_PRICE", "0.006")) / 1000,
            },
            "gpt-4": {
                "input": float(os.getenv("AZURE_GPT4_INPUT_PRICE", "0.03")) / 1000,
                "output": float(os.getenv("AZURE_GPT4_OUTPUT_PRICE", "0.06")) / 1000,
            },
            "gpt-35-turbo": {
                "input": float(os.getenv("AZURE_GPT35_TURBO_INPUT_PRICE", "0.0015")) / 1000,
                "output": float(os.getenv("AZURE_GPT35_TURBO_OUTPUT_PRICE", "0.002")) / 1000,
            },
        }

    @property
    def PRICING(self) -> dict[str, dict[str, float]]:
        """Get current pricing configuration (property for backward compatibility)."""
        return self._get_pricing()

    def __init__(self, db_path: Path | None = None):
        """Initialize cost tracker with SQLite database.

        Args:
            db_path: Path to SQLite database. If None, uses BRAIN_COST_DB_PATH env var or ~/.brain/costs.db
        """
        if db_path is None:
            # Check environment variable first
            env_path = os.getenv("BRAIN_COST_DB_PATH")
            if env_path:
                db_path = Path(env_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)
            else:
                # Default to ~/.brain/costs.db
                brain_dir = Path.home() / ".brain"
                brain_dir.mkdir(exist_ok=True)
                db_path = brain_dir / "costs.db"

        self.db_path = db_path

        logger.debug(f"Cost tracker database: {self.db_path}")
        self._init_database()

    def _init_database(self) -> None:
        """Initialize the SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS llm_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    model TEXT NOT NULL,
                    prompt_tokens INTEGER NOT NULL,
                    completion_tokens INTEGER NOT NULL,
                    total_tokens INTEGER NOT NULL,
                    elapsed_seconds REAL NOT NULL,
                    estimated_cost REAL NOT NULL,
                    entry_date TEXT,
                    metadata TEXT
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON llm_usage(timestamp)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_operation
                ON llm_usage(operation)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entry_date
                ON llm_usage(entry_date)
            """)

            # Composite index for common queries (operation + time range)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_operation_timestamp
                ON llm_usage(operation, timestamp)
            """)

            # Enable WAL mode for better concurrent access
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost for a model call.

        Args:
            model: Model name (e.g., 'gpt-4o', 'gpt-4o-mini')
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens

        Returns:
            Estimated cost in USD
        """
        # Normalize model name (handle deployment names)
        model_key = model.lower()
        if "gpt-4o-mini" in model_key:
            model_key = "gpt-4o-mini"
        elif "gpt-4o" in model_key:
            model_key = "gpt-4o"
        elif "gpt-4" in model_key:
            model_key = "gpt-4"
        elif "gpt-35" in model_key or "gpt-3.5" in model_key:
            model_key = "gpt-35-turbo"

        pricing_data = self._get_pricing()
        pricing = pricing_data.get(model_key, pricing_data["gpt-4o"])  # Default to gpt-4o

        input_cost = prompt_tokens * pricing["input"]
        output_cost = completion_tokens * pricing["output"]

        return input_cost + output_cost

    def record_usage(
        self,
        operation: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        elapsed_seconds: float,
        entry_date: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Record an LLM usage event.

        Args:
            operation: Type of operation (backlinks, tags, reports, etc.)
            model: Model used
            prompt_tokens: Number of input tokens
            completion_tokens: Number of output tokens
            elapsed_seconds: Time taken for the operation
            entry_date: Date of diary entry being processed (if applicable)
            metadata: Additional context data
        """
        total_tokens = prompt_tokens + completion_tokens
        estimated_cost = self.calculate_cost(model, prompt_tokens, completion_tokens)

        usage = LLMUsage(
            timestamp=datetime.now(),
            operation=operation,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            elapsed_seconds=elapsed_seconds,
            estimated_cost=estimated_cost,
            entry_date=entry_date,
            metadata=metadata,
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO llm_usage (
                    timestamp, operation, model, prompt_tokens, completion_tokens,
                    total_tokens, elapsed_seconds, estimated_cost, entry_date, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    usage.timestamp.isoformat(),
                    usage.operation,
                    usage.model,
                    usage.prompt_tokens,
                    usage.completion_tokens,
                    usage.total_tokens,
                    usage.elapsed_seconds,
                    usage.estimated_cost,
                    usage.entry_date,
                    json.dumps(usage.metadata) if usage.metadata else None,
                ),
            )

        logger.debug(f"Recorded usage: {operation} ${estimated_cost:.4f}")

    def get_summary(
        self, days: int | None = 30, start_date: date | None = None, end_date: date | None = None
    ) -> CostSummary:
        """Get cost summary for a time period.

        Args:
            days: Number of days to look back (ignored if start_date/end_date provided)
            start_date: Start date for summary
            end_date: End date for summary (inclusive)

        Returns:
            CostSummary with aggregated data
        """
        if start_date is None and end_date is None:
            end_date = date.today()
            start_date = end_date - timedelta(days=days or 30)
        elif start_date is None:
            if end_date is not None:
                start_date = end_date - timedelta(days=days or 30)
            else:
                end_date = date.today()
                start_date = end_date - timedelta(days=days or 30)
        elif end_date is None:
            end_date = date.today()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT * FROM llm_usage
                WHERE date(timestamp) BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """,
                (start_date.isoformat(), end_date.isoformat()),
            )

            records = cursor.fetchall()

        if not records:
            return CostSummary(0.0, 0, 0, {}, {})

        total_cost = 0.0
        total_tokens = 0
        total_requests = len(records)
        by_operation = {}
        by_day = {}

        for record in records:
            cost = record["estimated_cost"]
            tokens = record["total_tokens"]
            operation = record["operation"]
            day = record["timestamp"][:10]  # Extract date part

            total_cost += cost
            total_tokens += tokens

            # By operation
            if operation not in by_operation:
                by_operation[operation] = {"cost": 0.0, "tokens": 0, "requests": 0}
            by_operation[operation]["cost"] += cost
            by_operation[operation]["tokens"] += tokens
            by_operation[operation]["requests"] += 1

            # By day
            if day not in by_day:
                by_day[day] = {"cost": 0.0, "tokens": 0, "requests": 0}
            by_day[day]["cost"] += cost
            by_day[day]["tokens"] += tokens
            by_day[day]["requests"] += 1

        return CostSummary(
            total_cost=total_cost,
            total_tokens=total_tokens,
            total_requests=total_requests,
            by_operation=by_operation,
            by_day=by_day,
        )

    def get_monthly_summary(self, year: int, month: int) -> CostSummary:
        """Get cost summary for a specific month.

        Args:
            year: Year (e.g., 2025)
            month: Month (1-12)

        Returns:
            CostSummary for the specified month
        """
        start_date = date(year, month, 1)

        # Get last day of month
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        return self.get_summary(start_date=start_date, end_date=end_date)

    def get_trends(self, days: int = 30) -> list[tuple[str, float]]:
        """Get daily cost trends.

        Args:
            days: Number of days to analyze

        Returns:
            List of (date, cost) tuples
        """
        summary = self.get_summary(days=days)

        # Fill in missing days with 0 cost
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        trends = []
        current_date = start_date

        while current_date <= end_date:
            date_str = current_date.isoformat()
            cost = summary.by_day.get(date_str, {}).get("cost", 0.0)
            trends.append((date_str, cost))
            current_date += timedelta(days=1)

        return trends

    def estimate_monthly_cost(self, days_sample: int = 7) -> float:
        """Estimate monthly cost based on recent usage.

        Args:
            days_sample: Number of recent days to base estimate on

        Returns:
            Estimated monthly cost in USD
        """
        summary = self.get_summary(days=days_sample)

        if summary.total_requests == 0:
            return 0.0

        daily_average = summary.total_cost / days_sample
        return daily_average * 30.44  # Average days per month

    def update_pricing(self, model: str, input_price: float, output_price: float) -> None:
        """Update pricing for a model (deprecated - use environment variables instead).

        Args:
            model: Model name
            input_price: Price per input token
            output_price: Price per output token
        """
        logger.warning(
            f"update_pricing is deprecated. Use environment variables instead:\n"
            f"AZURE_{model.upper().replace('-', '_')}_INPUT_PRICE={input_price * 1000}\n"
            f"AZURE_{model.upper().replace('-', '_')}_OUTPUT_PRICE={output_price * 1000}"
        )

    def export_data(
        self, start_date: date | None = None, end_date: date | None = None
    ) -> list[dict]:
        """Export usage data as JSON-serializable list.

        Args:
            start_date: Start date for export
            end_date: End date for export

        Returns:
            List of usage records as dictionaries
        """
        if start_date is None:
            start_date = date.today() - timedelta(days=365)
        if end_date is None:
            end_date = date.today()

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            cursor = conn.execute(
                """
                SELECT * FROM llm_usage
                WHERE date(timestamp) BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """,
                (start_date.isoformat(), end_date.isoformat()),
            )

            records = cursor.fetchall()

        return [dict(record) for record in records]


# Global cost tracker instance
_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker
