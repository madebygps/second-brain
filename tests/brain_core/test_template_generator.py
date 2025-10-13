"""Tests for template_generator module."""
import pytest
from unittest.mock import Mock
from datetime import date

from brain_core.template_generator import (
    generate_planning_prompts,
    is_sunday
)
from brain_core.entry_manager import DiaryEntry


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_is_sunday(self):
        """Test Sunday detection."""
        # 2025-10-12 is a Sunday
        sunday = date(2025, 10, 12)
        assert is_sunday(sunday)

        # 2025-10-13 is a Monday
        monday = date(2025, 10, 13)
        assert not is_sunday(monday)


class TestPlanningPrompts:
    """Tests for planning prompt generation."""

    def test_generate_planning_prompts_with_entry(self):
        """Test generating planning prompts from yesterday's entry."""
        yesterday_entry = DiaryEntry(
            date(2025, 10, 11),
            """## Brain Dump
I had a great session teaching Python today. Need to follow up on the project proposal.
Also discussed the new feature with the team. Should prepare for tomorrow's meeting.
"""
        )

        mock_llm = Mock()
        mock_llm.generate_sync.return_value = """1. Based on [[2025-10-11]], how will you follow up on the project proposal?
2. What preparation do you need for tomorrow's meeting?
3. What are your main priorities for the Python teaching session?"""

        prompts = generate_planning_prompts(yesterday_entry, mock_llm)

        assert len(prompts) == 3
        assert "[[2025-10-11]]" in prompts[0]
        assert mock_llm.generate_sync.called

    def test_generate_planning_prompts_no_entry(self):
        """Test generating planning prompts with no yesterday entry."""
        mock_llm = Mock()

        prompts = generate_planning_prompts(None, mock_llm)

        # Should return default prompts without calling LLM
        assert len(prompts) == 3
        assert "priorities" in prompts[0].lower()
        assert not mock_llm.generate_sync.called

    def test_generate_planning_prompts_empty_entry(self):
        """Test generating planning prompts with empty brain dump."""
        empty_entry = DiaryEntry(date(2025, 10, 11), "## Brain Dump\n")

        mock_llm = Mock()

        prompts = generate_planning_prompts(empty_entry, mock_llm)

        # Should return default prompts without calling LLM
        assert len(prompts) == 3
        assert not mock_llm.generate_sync.called

    def test_generate_planning_prompts_handles_llm_failure(self):
        """Test handling LLM failure gracefully."""
        yesterday_entry = DiaryEntry(
            date(2025, 10, 11),
            """## Brain Dump
Test content here.
"""
        )

        mock_llm = Mock()
        mock_llm.generate_sync.side_effect = RuntimeError("LLM connection failed")

        prompts = generate_planning_prompts(yesterday_entry, mock_llm)

        # Should return default prompts
        assert len(prompts) == 3
        assert "priorities" in prompts[0].lower()

    def test_generate_planning_prompts_handles_malformed_response(self):
        """Test handling malformed LLM response."""
        yesterday_entry = DiaryEntry(
            date(2025, 10, 11),
            """## Brain Dump
Test content.
"""
        )

        mock_llm = Mock()
        # LLM returns malformed response (no numbered items)
        mock_llm.generate_sync.return_value = "This is not a proper response"

        prompts = generate_planning_prompts(yesterday_entry, mock_llm)

        # Should still return 3 prompts (with fallback)
        assert len(prompts) == 3

    def test_generate_planning_prompts_pads_insufficient_prompts(self):
        """Test padding when LLM returns too few prompts."""
        yesterday_entry = DiaryEntry(
            date(2025, 10, 11),
            """## Brain Dump
Test content.
"""
        )

        mock_llm = Mock()
        # LLM returns only 1 prompt instead of 3
        mock_llm.generate_sync.return_value = "1. Based on [[2025-10-11]], what will you do?"

        prompts = generate_planning_prompts(yesterday_entry, mock_llm)

        # Should pad to 3 prompts
        assert len(prompts) == 3
        assert "[[2025-10-11]]" in prompts[0]
        assert "attention" in prompts[1].lower() or "attention" in prompts[2].lower()

    def test_generate_planning_prompts_truncates_excess_prompts(self):
        """Test truncating when LLM returns too many prompts."""
        yesterday_entry = DiaryEntry(
            date(2025, 10, 11),
            """## Brain Dump
Test content.
"""
        )

        mock_llm = Mock()
        # LLM returns 5 prompts instead of 3
        mock_llm.generate_sync.return_value = """1. First prompt [[2025-10-11]]
2. Second prompt
3. Third prompt
4. Fourth prompt
5. Fifth prompt"""

        prompts = generate_planning_prompts(yesterday_entry, mock_llm)

        # Should only keep first 3
        assert len(prompts) == 3
        assert "First prompt" in prompts[0]
        assert "Second prompt" in prompts[1]
        assert "Third prompt" in prompts[2]
