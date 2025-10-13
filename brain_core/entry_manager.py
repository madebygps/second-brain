"""Manage diary entry files (read/write markdown)."""

import re
from datetime import date, timedelta
from pathlib import Path

from .constants import MIN_SUBSTANTIAL_CONTENT_CHARS


class DiaryEntry:
    """Represents a single diary entry."""

    def __init__(self, entry_date: date, content: str = "", entry_type: str = "reflection"):
        self.date = entry_date
        self.content = content
        self.entry_type = entry_type  # "reflection" or "plan"
        self._reflection_prompts: str | None = None
        self._brain_dump: str | None = None
        self._memory_links: str | None = None

    @property
    def filename(self) -> str:
        """Get filename for this entry (YYYY-MM-DD.md or YYYY-MM-DD-plan.md)."""
        if self.entry_type == "plan":
            return f"{self.date.isoformat()}-plan.md"
        return f"{self.date.isoformat()}.md"

    def parse_sections(self) -> None:
        """Parse content into sections."""
        # Extract Reflection Prompts section
        reflection_match = re.search(
            r"## Reflection Prompts\n(.*?)(?=\n---|\n##|$)", self.content, re.DOTALL
        )
        if reflection_match:
            self._reflection_prompts = reflection_match.group(1).strip()

        # Extract Brain Dump section
        brain_dump_match = re.search(
            r"## Brain Dump\n(.*?)(?=\n---|\n##|$)", self.content, re.DOTALL
        )
        if brain_dump_match:
            self._brain_dump = brain_dump_match.group(1).strip()

        # Extract Memory Links section
        memory_links_match = re.search(r"## Memory Links\n(.*?)$", self.content, re.DOTALL)
        if memory_links_match:
            self._memory_links = memory_links_match.group(1).strip()

    @property
    def brain_dump(self) -> str:
        """Get brain dump content."""
        if self._brain_dump is None:
            self.parse_sections()
        return self._brain_dump or ""

    @property
    def has_substantial_content(self) -> bool:
        """Check if entry has substantial content in brain dump."""
        return len(self.brain_dump) > MIN_SUBSTANTIAL_CONTENT_CHARS

    def get_backlinks(self) -> list[str]:
        """Extract all [[backlinks]] from content."""
        return re.findall(r"\[\[([^\]]+)\]\]", self.content)

    def get_tags(self) -> list[str]:
        """Extract all #tags from content."""
        return re.findall(r"#(\w+)", self.content)


class EntryManager:
    """Manage reading and writing diary entries."""

    def __init__(self, diary_path: Path, planner_path: Path | None = None):
        self.diary_path = diary_path
        self.planner_path = planner_path if planner_path else diary_path

    def get_entry_path(self, entry_date: date, entry_type: str = "reflection") -> Path:
        """Get full path for a diary entry."""
        if entry_type == "plan":
            filename = f"{entry_date.isoformat()}-plan.md"
            return self.planner_path / filename
        else:
            filename = f"{entry_date.isoformat()}.md"
            return self.diary_path / filename

    def entry_exists(self, entry_date: date, entry_type: str = "reflection") -> bool:
        """Check if entry exists for given date and type."""
        return self.get_entry_path(entry_date, entry_type).exists()

    def read_entry(self, entry_date: date, entry_type: str = "reflection") -> DiaryEntry | None:
        """Read diary entry for given date and type."""
        path = self.get_entry_path(entry_date, entry_type)
        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8")
        return DiaryEntry(entry_date, content, entry_type)

    def write_entry(self, entry: DiaryEntry) -> None:
        """Write diary entry to file."""
        path = self.get_entry_path(entry.date, entry.entry_type)
        path.write_text(entry.content, encoding="utf-8")

    def create_entry_template(self, entry_date: date, prompts: list[str]) -> DiaryEntry:
        """Create a new entry with template structure (prompts + brain dump only)."""
        sections = []

        # Reflection Prompts section
        sections.append("## Reflection Prompts")
        for i, prompt in enumerate(prompts, 1):
            sections.append(f"**{i}. {prompt}**")
            sections.append("")
        sections.append("---")
        sections.append("")

        # Brain Dump section
        sections.append("## Brain Dump")
        sections.append("")

        content = "\n".join(sections)
        return DiaryEntry(entry_date, content)

    def create_plan_template(
        self, entry_date: date, prompts: list[str], pending_todos: list[str] = None
    ) -> DiaryEntry:
        """Create a new plan entry with template structure."""
        sections = []

        # Daily Focus section
        sections.append("## Daily Focus")
        for i, prompt in enumerate(prompts, 1):
            sections.append(f"**{i}. {prompt}**")
            sections.append("")
        sections.append("---")
        sections.append("")

        # Action Items section
        sections.append("## Action Items")
        if pending_todos:
            for todo in pending_todos:
                sections.append(f"- [ ] {todo}")
        else:
            sections.append("- [ ] ")
        sections.append("")
        sections.append("---")
        sections.append("")

        # Brain Dump section
        sections.append("## Brain Dump")
        sections.append("")

        content = "\n".join(sections)
        return DiaryEntry(entry_date, content, entry_type="plan")

    def list_entries(self, days: int = 30) -> list[DiaryEntry]:
        """List recent entries (up to N days back)."""
        entries = []
        today = date.today()
        cutoff_date = today - timedelta(days=days)

        # Use glob to find existing markdown files
        for path in sorted(self.diary_path.glob("*.md"), reverse=True):
            try:
                # Parse date from filename (YYYY-MM-DD.md)
                date_str = path.stem
                entry_date = date.fromisoformat(date_str)

                # Only include entries within date range
                if cutoff_date <= entry_date <= today:
                    content = path.read_text(encoding="utf-8")
                    entries.append(DiaryEntry(entry_date, content))
            except (ValueError, OSError):
                # Skip files that don't match date format or can't be read
                continue

        return entries

    def get_past_calendar_days(self, from_date: date, num_days: int) -> list[date]:
        """Get past N calendar days (not last N entries)."""
        dates = []
        for i in range(1, num_days + 1):
            dates.append(from_date - timedelta(days=i))
        return dates

    def get_entries_for_dates(self, dates: list[date]) -> list[DiaryEntry]:
        """Get entries for specific dates (only existing ones)."""
        entries = []
        for entry_date in dates:
            entry = self.read_entry(entry_date)
            if entry and entry.has_substantial_content:
                entries.append(entry)
        return entries

    def update_memory_links(
        self,
        entry: DiaryEntry,
        temporal_links: list[str],
        topic_tags: list[str],
        link_metadata: dict = None,
    ) -> DiaryEntry:
        """Update the Memory Links section of an entry.

        Args:
            link_metadata: Optional dict mapping date -> {"confidence": str, "reason": str}
                          for displaying link explanations
        """
        # Parse existing content
        entry.parse_sections()

        # Build new Memory Links section
        memory_lines = ["## Memory Links"]

        if temporal_links:
            if link_metadata:
                # Enhanced format with confidence and reasons
                memory_lines.append("**Temporal:**")
                for link in temporal_links:
                    meta = link_metadata.get(link, {})
                    confidence = meta.get("confidence", "")
                    reason = meta.get("reason", "")

                    link_str = f"- [[{link}]]"
                    if confidence:
                        confidence_marker = {"high": "**", "medium": "*", "low": "~"}.get(
                            confidence, "*"
                        )
                        link_str += f" {confidence_marker}"
                    if reason:
                        link_str += f" *{reason}*"

                    memory_lines.append(link_str)
            else:
                # Legacy simple format
                links_str = " • ".join([f"[[{link}]]" for link in temporal_links])
                memory_lines.append(f"**Temporal:** {links_str}")

        if topic_tags:
            tags_str = " ".join([f"#{tag}" for tag in topic_tags])
            memory_lines.append(f"**Topics:** {tags_str}")

        new_memory_section = "\n".join(memory_lines)

        # Replace or append Memory Links section
        if "## Memory Links" in entry.content:
            # Replace existing section
            new_content = re.sub(
                r"## Memory Links\n.*$", new_memory_section, entry.content, flags=re.DOTALL
            )
        else:
            # Append new section
            new_content = entry.content.rstrip() + "\n\n" + new_memory_section

        entry.content = new_content
        return entry


def extract_todos(entry: DiaryEntry) -> list[str]:
    """Extract action items/todos from entry content using regex patterns.

    Args:
        entry: Diary entry to extract todos from

    Returns:
        List of todo strings found in the entry
    """
    todos = []

    # Look for common todo patterns
    patterns = [
        r"(?:^|\n)[-*•]\s*(?:TODO|To do|Action):\s*(.+?)(?:\n|$)",  # - TODO: item
        r"(?:^|\n)[-*•]\s*\[ \]\s*(.+?)(?:\n|$)",  # - [ ] item (checkbox)
        r"(?:^|\n)(?:TODO|To do|Action):\s*(.+?)(?:\n|$)",  # TODO: item
        r"(?:^|\n)(?:I need to|I should|I must|I will)\s+(.+?)(?:\.|$)",  # Natural language
    ]

    content = entry.content

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            todo = match.group(1).strip()
            if todo and len(todo) > 3:  # Filter out very short matches
                todos.append(todo)

    return todos
