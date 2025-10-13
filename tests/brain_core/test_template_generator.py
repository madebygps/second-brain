"""Tests for template_generator module."""
import pytest
from unittest.mock import Mock
from datetime import date

from brain_core.template_generator import is_sunday


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
