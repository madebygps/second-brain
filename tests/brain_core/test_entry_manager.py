"""Tests for entry_manager module - Only essential tests to prevent data loss."""
from datetime import date

from brain_core.entry_manager import DiaryEntry, EntryManager


class TestDiaryEntry:
    """Essential tests for DiaryEntry to prevent data corruption."""

    def test_reflection_entry_filename(self):
        """Test filename generation for reflection entry - prevents wrong file writes."""
        entry = DiaryEntry(date(2025, 10, 12), entry_type="reflection")
        assert entry.filename == "2025-10-12.md"

    def test_plan_entry_filename(self):
        """Test filename generation for plan entry - prevents wrong file writes."""
        entry = DiaryEntry(date(2025, 10, 12), entry_type="plan")
        assert entry.filename == "2025-10-12-plan.md"


class TestEntryManager:
    """Essential tests for EntryManager to prevent data loss."""

    def test_separate_planner_path(self, temp_dir):
        """Test EntryManager respects separate paths - critical for file organization."""
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

    def test_write_and_read_reflection_entry(self, temp_dir):
        """Test basic write/read cycle - prevents data loss."""
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
        """Test plan write/read cycle - prevents data loss."""
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
