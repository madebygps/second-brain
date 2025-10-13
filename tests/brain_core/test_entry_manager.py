"""Tests for entry_manager module."""
import pytest
from datetime import date, timedelta
from pathlib import Path

from brain_core.entry_manager import DiaryEntry, EntryManager


class TestDiaryEntry:
    """Tests for DiaryEntry class."""

    def test_reflection_entry_filename(self):
        """Test filename generation for reflection entry."""
        entry = DiaryEntry(date(2025, 10, 12), entry_type="reflection")
        assert entry.filename == "2025-10-12.md"

    def test_plan_entry_filename(self):
        """Test filename generation for plan entry."""
        entry = DiaryEntry(date(2025, 10, 12), entry_type="plan")
        assert entry.filename == "2025-10-12-plan.md"

    def test_default_entry_type(self):
        """Test default entry type is reflection."""
        entry = DiaryEntry(date(2025, 10, 12))
        assert entry.entry_type == "reflection"
        assert entry.filename == "2025-10-12.md"

    def test_parse_reflection_sections(self):
        """Test parsing reflection entry sections."""
        content = """## Reflection Prompts
**1. What did you learn today?**

---

## Brain Dump
Today was productive.

---

## Memory Links
**Temporal:** [[2025-10-11]]
**Topics:** #productivity
"""
        entry = DiaryEntry(date(2025, 10, 12), content)
        entry.parse_sections()

        assert "What did you learn today?" in entry._reflection_prompts
        assert "Today was productive." in entry._brain_dump
        assert "[[2025-10-11]]" in entry._memory_links

    def test_brain_dump_property(self):
        """Test brain_dump property extraction."""
        content = """## Brain Dump
This is my brain dump content with more than 50 characters to test substantial content.
"""
        entry = DiaryEntry(date(2025, 10, 12), content)
        assert "This is my brain dump content" in entry.brain_dump

    def test_has_substantial_content(self):
        """Test substantial content detection."""
        # Entry with substantial content
        long_content = """## Brain Dump
This is a long brain dump with more than 50 characters of actual content.
"""
        entry = DiaryEntry(date(2025, 10, 12), long_content)
        assert entry.has_substantial_content

        # Entry with minimal content (empty brain dump)
        short_content = """## Brain Dump

"""
        entry = DiaryEntry(date(2025, 10, 12), short_content)
        assert not entry.has_substantial_content

    def test_get_backlinks(self):
        """Test backlink extraction."""
        content = """## Brain Dump
Today I thought about [[2025-10-11]] and [[2025-10-10]].
"""
        entry = DiaryEntry(date(2025, 10, 12), content)
        backlinks = entry.get_backlinks()
        assert "2025-10-11" in backlinks
        assert "2025-10-10" in backlinks
        assert len(backlinks) == 2

    def test_get_tags(self):
        """Test tag extraction."""
        content = """## Memory Links
**Topics:** #productivity #learning #focus
"""
        entry = DiaryEntry(date(2025, 10, 12), content)
        tags = entry.get_tags()
        assert "productivity" in tags
        assert "learning" in tags
        assert "focus" in tags


class TestEntryManager:
    """Tests for EntryManager class."""

    def test_get_entry_path_reflection(self, temp_dir):
        """Test entry path for reflection entry."""
        manager = EntryManager(temp_dir)
        path = manager.get_entry_path(date(2025, 10, 12), entry_type="reflection")
        assert path == temp_dir / "2025-10-12.md"

    def test_get_entry_path_plan(self, temp_dir):
        """Test entry path for plan entry."""
        manager = EntryManager(temp_dir)
        path = manager.get_entry_path(date(2025, 10, 12), entry_type="plan")
        assert path == temp_dir / "2025-10-12-plan.md"

    def test_separate_planner_path(self, temp_dir):
        """Test EntryManager with separate planner_path."""
        diary_dir = temp_dir / "diary"
        planner_dir = temp_dir / "planner"
        diary_dir.mkdir()
        planner_dir.mkdir()

        manager = EntryManager(diary_dir, planner_dir)

        # Reflection should go to diary_path
        reflection_path = manager.get_entry_path(date(2025, 10, 12), entry_type="reflection")
        assert reflection_path == diary_dir / "2025-10-12.md"

        # Plan should go to planner_path
        plan_path = manager.get_entry_path(date(2025, 10, 12), entry_type="plan")
        assert plan_path == planner_dir / "2025-10-12-plan.md"

    def test_planner_path_defaults_to_diary_path(self, temp_dir):
        """Test that planner_path defaults to diary_path if not specified."""
        manager = EntryManager(temp_dir)

        # Both should use the same path
        reflection_path = manager.get_entry_path(date(2025, 10, 12), entry_type="reflection")
        plan_path = manager.get_entry_path(date(2025, 10, 12), entry_type="plan")
        
        assert reflection_path.parent == plan_path.parent
        assert reflection_path.parent == temp_dir

    def test_write_entry_to_separate_paths(self, temp_dir):
        """Test writing entries to separate diary and planner paths."""
        diary_dir = temp_dir / "diary"
        planner_dir = temp_dir / "planner"
        diary_dir.mkdir()
        planner_dir.mkdir()

        manager = EntryManager(diary_dir, planner_dir)
        test_date = date(2025, 10, 12)

        # Write reflection entry
        reflection = DiaryEntry(test_date, "Reflection content", entry_type="reflection")
        manager.write_entry(reflection)
        assert (diary_dir / "2025-10-12.md").exists()
        assert not (planner_dir / "2025-10-12.md").exists()

        # Write plan entry
        plan = DiaryEntry(test_date, "Plan content", entry_type="plan")
        manager.write_entry(plan)
        assert (planner_dir / "2025-10-12-plan.md").exists()
        assert not (diary_dir / "2025-10-12-plan.md").exists()

    def test_read_entry_from_separate_paths(self, temp_dir):
        """Test reading entries from separate diary and planner paths."""
        diary_dir = temp_dir / "diary"
        planner_dir = temp_dir / "planner"
        diary_dir.mkdir()
        planner_dir.mkdir()

        manager = EntryManager(diary_dir, planner_dir)
        test_date = date(2025, 10, 12)

        # Write entries to separate directories
        (diary_dir / "2025-10-12.md").write_text("Reflection content")
        (planner_dir / "2025-10-12-plan.md").write_text("Plan content")

        # Read reflection from diary_path
        reflection = manager.read_entry(test_date, entry_type="reflection")
        assert reflection is not None
        assert reflection.content == "Reflection content"

        # Read plan from planner_path
        plan = manager.read_entry(test_date, entry_type="plan")
        assert plan is not None
        assert plan.content == "Plan content"

    def test_entry_exists_reflection(self, temp_dir):
        """Test entry_exists for reflection entry."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)

        # Entry doesn't exist yet
        assert not manager.entry_exists(test_date, entry_type="reflection")

        # Create entry
        path = manager.get_entry_path(test_date, entry_type="reflection")
        path.write_text("test content")

        # Entry exists now
        assert manager.entry_exists(test_date, entry_type="reflection")

    def test_entry_exists_plan(self, temp_dir):
        """Test entry_exists for plan entry."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)

        # Plan entry doesn't exist yet
        assert not manager.entry_exists(test_date, entry_type="plan")

        # Create plan entry
        path = manager.get_entry_path(test_date, entry_type="plan")
        path.write_text("test content")

        # Plan entry exists now
        assert manager.entry_exists(test_date, entry_type="plan")

    def test_write_and_read_reflection_entry(self, temp_dir):
        """Test writing and reading reflection entry."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)

        # Create and write entry
        entry = DiaryEntry(test_date, "Test reflection content", entry_type="reflection")
        manager.write_entry(entry)

        # Read entry back
        read_entry = manager.read_entry(test_date, entry_type="reflection")
        assert read_entry is not None
        assert read_entry.content == "Test reflection content"
        assert read_entry.entry_type == "reflection"

    def test_write_and_read_plan_entry(self, temp_dir):
        """Test writing and reading plan entry."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)

        # Create and write plan entry
        entry = DiaryEntry(test_date, "Test plan content", entry_type="plan")
        manager.write_entry(entry)

        # Read entry back
        read_entry = manager.read_entry(test_date, entry_type="plan")
        assert read_entry is not None
        assert read_entry.content == "Test plan content"
        assert read_entry.entry_type == "plan"

    def test_create_entry_template(self, temp_dir):
        """Test creating reflection entry template."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)
        prompts = [
            "What did you learn today?",
            "What are you grateful for?",
            "What will you do differently tomorrow?"
        ]

        entry = manager.create_entry_template(test_date, prompts)

        assert entry.date == test_date
        assert "## Reflection Prompts" in entry.content
        assert "## Brain Dump" in entry.content
        assert "What did you learn today?" in entry.content
        assert "What are you grateful for?" in entry.content

    def test_create_plan_template(self, temp_dir):
        """Test creating plan entry template."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)
        prompts = [
            "What are your main priorities?",
            "What meetings need preparation?",
            "What unfinished items need attention?"
        ]

        entry = manager.create_plan_template(test_date, prompts)

        assert entry.date == test_date
        assert entry.entry_type == "plan"
        assert "## Daily Focus" in entry.content
        assert "## Action Items" in entry.content
        assert "## Brain Dump" in entry.content
        assert "What are your main priorities?" in entry.content

    def test_create_plan_template_with_pending_todos(self, temp_dir):
        """Test creating plan entry with pending todos."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)
        prompts = ["What are your priorities?"]
        pending_todos = [
            "Finish project (from [[2025-10-11]])",
            "Review PR (from [[2025-10-11]])"
        ]

        entry = manager.create_plan_template(test_date, prompts, pending_todos)

        assert "Finish project (from [[2025-10-11]])" in entry.content
        assert "Review PR (from [[2025-10-11]])" in entry.content
        assert "- [ ] Finish project" in entry.content
        assert "- [ ] Review PR" in entry.content

    def test_list_entries(self, temp_dir):
        """Test listing recent entries."""
        manager = EntryManager(temp_dir)

        # Create several entries
        today = date.today()
        for i in range(5):
            entry_date = today - timedelta(days=i)
            entry = DiaryEntry(entry_date, f"Content {i}")
            manager.write_entry(entry)

        # List entries
        entries = manager.list_entries(days=7)

        assert len(entries) == 5
        assert all(isinstance(e, DiaryEntry) for e in entries)
        # Entries should be sorted newest first
        assert entries[0].date >= entries[-1].date

    def test_list_entries_excludes_plan_files(self, temp_dir):
        """Test that list_entries only returns reflection entries by default."""
        manager = EntryManager(temp_dir)
        test_date = date.today()

        # Create both reflection and plan entries
        reflection = DiaryEntry(test_date, "Reflection", entry_type="reflection")
        plan = DiaryEntry(test_date, "Plan", entry_type="plan")

        manager.write_entry(reflection)
        manager.write_entry(plan)

        # List entries should only get reflection entries
        entries = manager.list_entries(days=1)

        # Should only get the reflection entry (*.md, not *-plan.md)
        assert len(entries) == 1
        assert entries[0].filename == f"{test_date.isoformat()}.md"

    def test_get_past_calendar_days(self, temp_dir):
        """Test getting past calendar days."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)

        past_dates = manager.get_past_calendar_days(test_date, 3)

        assert len(past_dates) == 3
        assert past_dates[0] == date(2025, 10, 11)
        assert past_dates[1] == date(2025, 10, 10)
        assert past_dates[2] == date(2025, 10, 9)

    def test_get_entries_for_dates(self, temp_dir):
        """Test getting entries for specific dates."""
        manager = EntryManager(temp_dir)

        # Create entries with proper markdown structure
        date1 = date(2025, 10, 12)
        date2 = date(2025, 10, 11)
        date3 = date(2025, 10, 10)

        # Create entries with Brain Dump section for proper parsing
        content1 = "## Brain Dump\n" + ("A" * 60)  # Substantial content
        content2 = "## Brain Dump\n" + ("B" * 60)  # Substantial content

        entry1 = DiaryEntry(date1, content1)
        entry2 = DiaryEntry(date2, content2)
        # Don't create entry for date3

        manager.write_entry(entry1)
        manager.write_entry(entry2)

        # Get entries for dates
        entries = manager.get_entries_for_dates([date1, date2, date3])

        # Should only get entries that exist with substantial content
        assert len(entries) == 2
        assert entries[0].date == date1
        assert entries[1].date == date2

    def test_update_memory_links(self, temp_dir):
        """Test updating memory links section."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)

        # Create entry with existing content
        content = """## Reflection Prompts
**1. Test prompt**

---

## Brain Dump
Test content
"""
        entry = DiaryEntry(test_date, content)

        # Update memory links
        temporal_links = ["2025-10-11", "2025-10-10"]
        topic_tags = ["productivity", "learning"]

        updated_entry = manager.update_memory_links(entry, temporal_links, topic_tags)

        assert "## Memory Links" in updated_entry.content
        assert "[[2025-10-11]]" in updated_entry.content
        assert "[[2025-10-10]]" in updated_entry.content
        assert "#productivity" in updated_entry.content
        assert "#learning" in updated_entry.content

    def test_update_memory_links_with_metadata(self, temp_dir):
        """Test updating memory links with confidence metadata."""
        manager = EntryManager(temp_dir)
        test_date = date(2025, 10, 12)

        content = """## Brain Dump
Test content
"""
        entry = DiaryEntry(test_date, content)

        temporal_links = ["2025-10-11"]
        topic_tags = ["productivity"]
        link_metadata = {
            "2025-10-11": {
                "confidence": "high",
                "reason": "Similar topics discussed"
            }
        }

        updated_entry = manager.update_memory_links(
            entry, temporal_links, topic_tags, link_metadata
        )

        # Check for enhanced format with confidence indicators
        assert "[[2025-10-11]]" in updated_entry.content
        assert "Similar topics discussed" in updated_entry.content
        # High confidence marker is **
        assert "[[2025-10-11]] **" in updated_entry.content
