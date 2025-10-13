"""Planning commands for daily task management."""

import logging
import re
import time
from datetime import date, timedelta

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from brain_core.config import get_config, get_llm_client
from brain_core.constants import TASK_EXTRACTION_MAX_TOKENS, TASK_EXTRACTION_TEMPERATURE
from brain_core.entry_manager import EntryManager

app = typer.Typer(help="Daily planning with task management")
console = Console()
logger = logging.getLogger(__name__)


def parse_date_arg(date_arg: str) -> date:
    """Parse date argument (today, tomorrow, or YYYY-MM-DD).

    Args:
        date_arg: Date string to parse ("today", "tomorrow", or "YYYY-MM-DD")

    Returns:
        Parsed date object
    """
    if date_arg.lower() == "today":
        return date.today()
    elif date_arg.lower() == "tomorrow":
        return date.today() + timedelta(days=1)
    else:
        return date.fromisoformat(date_arg)


def extract_tasks_from_diary(diary_entry_content: str, diary_date: str, llm_client) -> list[str]:
    """Extract actionable tasks from yesterday's diary entry using LLM.

    Args:
        diary_entry_content: Content of yesterday's diary entry
        diary_date: ISO format date of the diary entry
        llm_client: LLM client for task extraction

    Returns:
        List of task strings extracted from the diary
    """
    if not diary_entry_content or len(diary_entry_content.strip()) < 50:
        return []

    system_prompt = """You are a task extraction assistant. Analyze diary entries and extract actionable tasks for today.

Extract tasks that:
- Are mentioned as incomplete, pending, or needing follow-up
- Represent specific actions (not vague intentions)
- Are relevant for the next day
- Include follow-ups from meetings or conversations

Do NOT extract:
- Completed activities (past tense)
- General reflections or feelings
- Vague intentions without clear actions

Format: Return ONLY a numbered list of tasks, one per line.
Example:
1. Follow up with Sarah about project proposal
2. Review and merge pull request #42
3. Prepare slides for Thursday presentation

If no actionable tasks are found, return: NO_TASKS"""

    user_prompt = f"""Analyze this diary entry from [[{diary_date}]] and extract actionable tasks for today:

{diary_entry_content}

Extract specific, actionable tasks that should be done today. Return as a numbered list or NO_TASKS if none found."""

    try:
        start_time = time.time()
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=TASK_EXTRACTION_TEMPERATURE,
            max_tokens=TASK_EXTRACTION_MAX_TOKENS,
            operation="task_extraction",
            entry_date=diary_date,
        )
        elapsed = time.time() - start_time

        # Parse tasks from response
        if "NO_TASKS" in response.upper():
            logger.debug(f"No tasks extracted from diary in {elapsed:.2f}s")
            return []

        tasks = []
        for line in response.split("\n"):
            line = line.strip()
            # Match numbered lists like "1. Task" or "1) Task"
            if line and line[0].isdigit():
                # Remove leading number and punctuation
                task = re.sub(r"^\d+[.)\s]+", "", line).strip()
                if task and len(task) > 5:  # Minimum task length
                    tasks.append(task)

        logger.debug(f"Extracted {len(tasks)} tasks from diary in {elapsed:.2f}s")
        return tasks

    except Exception as e:
        logger.warning(f"Failed to extract tasks from diary: {e}")
        return []


@app.command()
def create(date_arg: str = typer.Argument("today", help="Date (today, tomorrow, or YYYY-MM-DD)")):
    """Create a daily plan with action items (extracts tasks from yesterday's diary and plan)."""
    try:
        config = get_config()
        entry_date = parse_date_arg(date_arg)

        entry_manager = EntryManager(config.diary_path, config.planner_path)

        # Check if plan entry already exists
        if entry_manager.entry_exists(entry_date, entry_type="plan"):
            console.print(f"[yellow]Plan for {entry_date.isoformat()} already exists[/yellow]")
            return

        yesterday_date = entry_date - timedelta(days=1)
        all_tasks = []

        # 1. Extract pending todos from yesterday's plan (if it exists)
        yesterday_plan = entry_manager.read_entry(yesterday_date, entry_type="plan")
        unchecked_count = 0
        if yesterday_plan:
            for line in yesterday_plan.content.split("\n"):
                if re.match(r"^- \[ \]", line.strip()):
                    todo_text = re.sub(r"^- \[ \]\s*", "", line.strip())
                    if todo_text:
                        all_tasks.append(f"{todo_text} (from [[{yesterday_date.isoformat()}]])")
                        unchecked_count += 1

        # 2. Extract tasks from yesterday's diary entry using LLM
        yesterday_diary = entry_manager.read_entry(yesterday_date, entry_type="reflection")
        extracted_count = 0
        if yesterday_diary and yesterday_diary.has_substantial_content:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                progress.add_task(
                    description="Analyzing yesterday's diary for tasks...", total=None
                )

                llm_client = get_llm_client()
                extracted_tasks = extract_tasks_from_diary(
                    yesterday_diary.brain_dump, yesterday_date.isoformat(), llm_client
                )

                for task in extracted_tasks:
                    # Add backlink to diary entry
                    task_with_link = f"{task} (from [[{yesterday_date.isoformat()}]])"
                    # Avoid duplicates
                    if task_with_link not in all_tasks and task not in all_tasks:
                        all_tasks.append(task_with_link)
                        extracted_count += 1

        # Create plan entry with all tasks
        sections = []
        sections.append("## Action Items")
        if all_tasks:
            for task in all_tasks:
                sections.append(f"- [ ] {task}")
        else:
            sections.append("- [ ] ")
        sections.append("")

        content = "\n".join(sections)

        from brain_core.entry_manager import DiaryEntry

        entry = DiaryEntry(entry_date, content, entry_type="plan")

        entry_manager.write_entry(entry)

        console.print(f"[green]✓[/green] Created plan: [bold]{entry.filename}[/bold]")
        console.print(f"[dim]Location: {config.planner_path / entry.filename}[/dim]")

        if unchecked_count > 0 or extracted_count > 0:
            summary_parts = []
            if unchecked_count > 0:
                summary_parts.append(f"{unchecked_count} pending from plan")
            if extracted_count > 0:
                summary_parts.append(f"{extracted_count} extracted from diary")
            console.print(f"[dim]Carried forward: {', '.join(summary_parts)}[/dim]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
