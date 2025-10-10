"""Manage diary entry files (read/write markdown)."""
from pathlib import Path
from datetime import date, datetime, timedelta
from typing import Optional, List
import re


class DiaryEntry:
    """Represents a single diary entry."""

    def __init__(self, entry_date: date, content: str = ""):
        self.date = entry_date
        self.content = content
        self._reflection_prompts: Optional[str] = None
        self._brain_dump: Optional[str] = None
        self._memory_links: Optional[str] = None

    @property
    def filename(self) -> str:
        """Get filename for this entry (YYYY-MM-DD.md)."""
        return f"{self.date.isoformat()}.md"

    def parse_sections(self) -> None:
        """Parse content into sections."""
        # Extract Reflection Prompts section
        reflection_match = re.search(
            r"## Reflection Prompts\n(.*?)(?=\n---|\n##|$)",
            self.content,
            re.DOTALL
        )
        if reflection_match:
            self._reflection_prompts = reflection_match.group(1).strip()

        # Extract Brain Dump section
        brain_dump_match = re.search(
            r"## Brain Dump\n(.*?)(?=\n---|\n##|$)",
            self.content,
            re.DOTALL
        )
        if brain_dump_match:
            self._brain_dump = brain_dump_match.group(1).strip()

        # Extract Memory Links section
        memory_links_match = re.search(
            r"## Memory Links\n(.*?)$",
            self.content,
            re.DOTALL
        )
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
        """Check if entry has >50 chars of actual writing in brain dump."""
        return len(self.brain_dump) > 50

    def get_backlinks(self) -> List[str]:
        """Extract all [[backlinks]] from content."""
        return re.findall(r"\[\[([^\]]+)\]\]", self.content)

    def get_tags(self) -> List[str]:
        """Extract all #tags from content."""
        return re.findall(r"#(\w+)", self.content)


class EntryManager:
    """Manage reading and writing diary entries."""

    def __init__(self, diary_path: Path):
        self.diary_path = diary_path

    def get_entry_path(self, entry_date: date) -> Path:
        """Get full path for a diary entry."""
        filename = f"{entry_date.isoformat()}.md"
        return self.diary_path / filename

    def entry_exists(self, entry_date: date) -> bool:
        """Check if entry exists for given date."""
        return self.get_entry_path(entry_date).exists()

    def read_entry(self, entry_date: date) -> Optional[DiaryEntry]:
        """Read diary entry for given date."""
        path = self.get_entry_path(entry_date)
        if not path.exists():
            return None

        content = path.read_text(encoding="utf-8")
        return DiaryEntry(entry_date, content)

    def write_entry(self, entry: DiaryEntry) -> None:
        """Write diary entry to file."""
        path = self.get_entry_path(entry.date)
        path.write_text(entry.content, encoding="utf-8")

    def create_entry_template(
        self,
        entry_date: date,
        prompts: List[str],
        temporal_links: Optional[List[str]] = None,
        tags: Optional[List[str]] = None
    ) -> DiaryEntry:
        """Create a new entry with template structure."""
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
        sections.append("---")
        sections.append("")

        # Memory Links section
        sections.append("## Memory Links")
        if temporal_links:
            links_str = " • ".join([f"[[{link}]]" for link in temporal_links])
            sections.append(f"**Temporal:** {links_str}")
        if tags:
            tags_str = " ".join([f"#{tag}" for tag in tags])
            sections.append(f"**Topics:** {tags_str}")

        content = "\n".join(sections)
        return DiaryEntry(entry_date, content)

    def list_entries(self, days: int = 30) -> List[DiaryEntry]:
        """List recent entries (up to N days back)."""
        entries = []
        today = date.today()

        for i in range(days):
            check_date = today - timedelta(days=i)
            entry = self.read_entry(check_date)
            if entry:
                entries.append(entry)

        return entries

    def get_past_calendar_days(self, from_date: date, num_days: int) -> List[date]:
        """Get past N calendar days (not last N entries)."""
        dates = []
        for i in range(1, num_days + 1):
            dates.append(from_date - timedelta(days=i))
        return dates

    def get_entries_for_dates(self, dates: List[date]) -> List[DiaryEntry]:
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
        temporal_links: List[str],
        topic_tags: List[str]
    ) -> DiaryEntry:
        """Update the Memory Links section of an entry."""
        # Parse existing content
        entry.parse_sections()

        # Build new Memory Links section
        memory_lines = ["## Memory Links"]
        if temporal_links:
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
                r"## Memory Links\n.*$",
                new_memory_section,
                entry.content,
                flags=re.DOTALL
            )
        else:
            # Append new section
            new_content = entry.content.rstrip() + "\n\n" + new_memory_section

        entry.content = new_content
        return entry
