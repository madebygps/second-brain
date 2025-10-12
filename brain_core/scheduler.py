"""Background daemon for automated diary tasks."""
import sys
from pathlib import Path
from datetime import date, time
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import signal

from brain_core.config import get_config, get_llm_client
from brain_core.entry_manager import EntryManager
from brain_core.analysis import create_memory_trace_report
from brain_core.llm_analysis import generate_semantic_backlinks, generate_semantic_tags
from brain_core.constants import (
    PAST_ENTRIES_LOOKBACK_DAYS,
    MIN_SUBSTANTIAL_CONTENT_CHARS
)


def auto_link_today():
    """Automatically link today's entry."""
    try:
        config = get_config()
        entry_manager = EntryManager(config.diary_path)
        today = date.today()

        entry = entry_manager.read_entry(today)
        if not entry:
            print(f"[{today}] No entry found for today. Skipping auto-link.")
            return

        if not entry.has_substantial_content:
            print(f"[{today}] Entry has insufficient content (<{MIN_SUBSTANTIAL_CONTENT_CHARS} chars). Skipping auto-link.")
            return

        # Initialize LLM client
        llm_client = get_llm_client()

        # Check LLM connection
        if not llm_client.check_connection_sync():
            print(f"[{today}] Error: Cannot connect to LLM provider ({config.llm_provider}). Skipping auto-link.")
            return

        # Get past entries
        past_entries = entry_manager.list_entries(days=PAST_ENTRIES_LOOKBACK_DAYS)

        # Use LLM to find semantic backlinks
        semantic_links = generate_semantic_backlinks(
            entry,
            past_entries,
            llm_client,
            max_links=5
        )

        # Generate topic tags using LLM
        tags = generate_semantic_tags([entry], llm_client, max_tags=5)

        # Get temporal links
        past_dates = entry_manager.get_past_calendar_days(today, 3)
        temporal_links = [d.isoformat() for d in past_dates if entry_manager.entry_exists(d)]

        # Add semantic links
        for link in semantic_links:
            if link not in temporal_links:
                temporal_links.append(link)

        # Update entry
        updated_entry = entry_manager.update_memory_links(entry, temporal_links, tags)
        entry_manager.write_entry(updated_entry)

        print(f"[{today}] ✓ Auto-linked today's entry ({len(temporal_links)} links, {len(tags)} tags)")

    except Exception as e:
        print(f"[{date.today()}] Error in auto_link_today: {e}")


def weekly_analysis():
    """Generate weekly memory trace analysis."""
    try:
        config = get_config()
        entry_manager = EntryManager(config.diary_path)

        # Analyze past 7 days
        entries = entry_manager.list_entries(days=7)

        if not entries:
            print(f"[{date.today()}] No entries found for weekly analysis.")
            return

        report = create_memory_trace_report(entries)

        # Save report to diary path
        report_filename = f"weekly-analysis-{date.today().isoformat()}.md"
        report_path = config.diary_path / report_filename

        report_path.write_text(report, encoding="utf-8")

        print(f"[{date.today()}] ✓ Generated weekly analysis: {report_filename}")

    except Exception as e:
        print(f"[{date.today()}] Error in weekly_analysis: {e}")


def bulk_refresh_links():
    """Refresh links for recent entries."""
    try:
        config = get_config()
        entry_manager = EntryManager(config.diary_path)

        # Initialize LLM client
        llm_client = get_llm_client()

        # Check LLM connection
        if not llm_client.check_connection_sync():
            print(f"[{date.today()}] Error: Cannot connect to LLM provider ({config.llm_provider}). Skipping bulk refresh.")
            return

        # Refresh past N days based on config
        refresh_days = config.daemon_refresh_days
        entries = entry_manager.list_entries(days=refresh_days)

        if not entries:
            print(f"[{date.today()}] No entries found for bulk refresh.")
            return

        count = 0
        past_entries = entry_manager.list_entries(days=PAST_ENTRIES_LOOKBACK_DAYS)

        for entry in entries:
            if not entry.has_substantial_content:
                continue

            # Use LLM to find semantic backlinks
            semantic_links = generate_semantic_backlinks(
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

            # Add semantic links
            for link in semantic_links:
                if link not in temporal_links:
                    temporal_links.append(link)

            # Update entry
            updated_entry = entry_manager.update_memory_links(entry, temporal_links, tags)
            entry_manager.write_entry(updated_entry)
            count += 1

        print(f"[{date.today()}] ✓ Bulk refresh complete ({count} entries updated)")

    except Exception as e:
        print(f"[{date.today()}] Error in bulk_refresh_links: {e}")


def run_daemon():
    """Run the daemon with scheduled tasks."""
    try:
        config = get_config()

        scheduler = BlockingScheduler()

        # Parse auto-link time (format: "HH:MM")
        hour, minute = map(int, config.daemon_auto_link_time.split(":"))

        # Schedule auto-linking at specified time daily
        scheduler.add_job(
            auto_link_today,
            CronTrigger(hour=hour, minute=minute),
            id="auto_link_daily",
            name="Auto-link today's entry"
        )

        # Schedule weekly analysis every Sunday at midnight
        if config.daemon_weekly_analysis:
            scheduler.add_job(
                weekly_analysis,
                CronTrigger(day_of_week='sun', hour=0, minute=5),
                id="weekly_analysis",
                name="Weekly memory trace analysis"
            )

        # Schedule bulk refresh every 7 days at 2am
        scheduler.add_job(
            bulk_refresh_links,
            CronTrigger(day_of_week='mon', hour=2, minute=0),
            id="bulk_refresh",
            name="Bulk refresh links"
        )

        # Handle graceful shutdown
        def shutdown(signum, frame):
            print("\n[Daemon] Shutting down...")
            scheduler.shutdown()
            sys.exit(0)

        signal.signal(signal.SIGINT, shutdown)
        signal.signal(signal.SIGTERM, shutdown)

        print("[Daemon] Starting diary daemon...")
        print(f"[Daemon] Auto-link scheduled at {config.daemon_auto_link_time} daily")
        if config.daemon_weekly_analysis:
            print("[Daemon] Weekly analysis scheduled for Sundays at 00:05")
        print("[Daemon] Bulk refresh scheduled for Mondays at 02:00")
        print("[Daemon] Press Ctrl+C to stop\n")

        scheduler.start()

    except Exception as e:
        print(f"[Daemon] Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_daemon()
