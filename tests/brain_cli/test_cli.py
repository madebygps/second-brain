"""Integration tests for CLI commands."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, timedelta
from typer.testing import CliRunner

from brain_cli.main import app as brain_app
from brain_cli.plan_commands import parse_date_arg, extract_tasks_from_diary


runner = CliRunner()


class TestBrainCLI:
    """Tests for main brain CLI."""

    def test_brain_help(self):
        """Test brain --help command."""
        result = runner.invoke(brain_app, ["--help"])
        assert result.exit_code == 0
        assert "brain" in result.stdout.lower()
        assert "diary" in result.stdout.lower()
        assert "notes" in result.stdout.lower()

    def test_diary_subcommand_help(self):
        """Test brain diary --help command."""
        result = runner.invoke(brain_app, ["diary", "--help"])
        assert result.exit_code == 0
        # Verify diary subcommands exist
        assert 'create' in result.stdout
        assert 'link' in result.stdout
        assert 'report' in result.stdout
        assert 'patterns' in result.stdout

    def test_notes_subcommand_help(self):
        """Test brain notes --help command."""
        result = runner.invoke(brain_app, ["notes", "--help"])
        assert result.exit_code == 0
        assert "search" in result.stdout.lower()
        assert "status" in result.stdout.lower()


class TestDiaryCommands:
    """Tests for diary commands."""

    @patch('brain_cli.diary_commands.get_config')
    @patch('brain_cli.diary_commands.get_llm_client')
    @patch('brain_cli.diary_commands.EntryManager')
    def test_diary_list_command(self, mock_manager, mock_llm, mock_config, mock_env):
        """Test diary list command."""
        # Setup mocks
        mock_config.return_value = Mock(
            diary_path=mock_env["diary_path"]
        )
        mock_manager.return_value.list_entries.return_value = []

        result = runner.invoke(brain_app, ["diary", "list", "7"])

        # Should run without error even with no entries
        assert "No entries found" in result.stdout or result.exit_code == 0

    @patch('brain_cli.diary_commands.get_config')
    @patch('brain_cli.diary_commands.get_llm_client')
    @patch('brain_cli.diary_commands.EntryManager')
    def test_diary_patterns_command(self, mock_manager, mock_llm, mock_config, mock_env):
        """Test diary patterns command."""
        mock_config.return_value = Mock(
            diary_path=mock_env["diary_path"]
        )
        mock_manager.return_value.list_entries.return_value = []

        result = runner.invoke(brain_app, ["diary", "patterns", "7"])

        assert "No entries found" in result.stdout or result.exit_code == 0

    @patch('brain_cli.plan_commands.get_config')
    @patch('brain_cli.plan_commands.EntryManager')
    def test_plan_command(self, mock_manager, mock_config, mock_env):
        """Test plan create command."""
        # Setup mocks
        mock_config.return_value = Mock(
            diary_path=mock_env["diary_path"],
            planner_path=mock_env["planner_path"]
        )

        mock_manager_instance = Mock()
        mock_manager_instance.entry_exists.return_value = False
        mock_manager_instance.read_entry.return_value = None
        mock_manager_instance.write_entry.return_value = None
        mock_manager.return_value = mock_manager_instance

        result = runner.invoke(brain_app, ["plan", "create", "2025-10-12"])

        assert result.exit_code == 0
        assert "Created plan" in result.stdout

    @patch('brain_cli.plan_commands.get_config')
    @patch('brain_cli.plan_commands.EntryManager')
    def test_plan_already_exists(self, mock_manager, mock_config, mock_env):
        """Test plan create command when entry already exists."""
        mock_config.return_value = Mock(
            diary_path=mock_env["diary_path"],
            planner_path=mock_env["planner_path"]
        )

        mock_manager_instance = Mock()
        mock_manager_instance.entry_exists.return_value = True
        mock_manager.return_value = mock_manager_instance

        result = runner.invoke(brain_app, ["plan", "create", "2025-10-12"])

        assert "already exists" in result.stdout.lower()

    @patch('brain_cli.plan_commands.get_config')
    @patch('brain_cli.plan_commands.get_llm_client')
    @patch('brain_cli.plan_commands.EntryManager')
    def test_plan_with_diary_tasks(self, mock_manager, mock_llm, mock_config, mock_env):
        """Test plan create with LLM task extraction from diary."""
        from brain_core.entry_manager import DiaryEntry
        
        # Setup mocks
        mock_config.return_value = Mock(
            diary_path=mock_env["diary_path"],
            planner_path=mock_env["planner_path"]
        )

        # Mock LLM to return tasks
        mock_llm_client = Mock()
        mock_llm_client.generate_sync.return_value = """1. Follow up with Sarah about project
2. Review pull request #42
3. Prepare slides for presentation"""
        mock_llm.return_value = mock_llm_client

        # Mock diary entry with substantial content
        yesterday_diary = DiaryEntry(
            date.today() - timedelta(days=1),
            "## Brain Dump\n" + "A" * 100,
            entry_type="reflection"
        )
        yesterday_diary._has_substantial_content = True

        mock_manager_instance = Mock()
        mock_manager_instance.entry_exists.return_value = False
        mock_manager_instance.read_entry.side_effect = lambda d, entry_type: (
            yesterday_diary if entry_type == "reflection" else None
        )
        mock_manager.return_value = mock_manager_instance

        result = runner.invoke(brain_app, ["plan", "create", "today"])

        assert result.exit_code == 0
        assert "Created plan" in result.stdout
        # Should show extracted tasks
        assert "extracted from diary" in result.stdout

    @patch('brain_cli.plan_commands.get_config')
    @patch('brain_cli.plan_commands.EntryManager')
    def test_plan_with_pending_todos(self, mock_manager, mock_config, mock_env):
        """Test plan create carries forward unchecked todos."""
        from brain_core.entry_manager import DiaryEntry
        
        mock_config.return_value = Mock(
            diary_path=mock_env["diary_path"],
            planner_path=mock_env["planner_path"]
        )

        # Mock yesterday's plan with unchecked todos
        yesterday_plan = DiaryEntry(
            date.today() - timedelta(days=1),
            """## Action Items
- [ ] Finish project documentation
- [x] Completed task
- [ ] Review team feedback""",
            entry_type="plan"
        )

        mock_manager_instance = Mock()
        mock_manager_instance.entry_exists.return_value = False
        mock_manager_instance.read_entry.side_effect = lambda d, entry_type: (
            yesterday_plan if entry_type == "plan" else None
        )
        mock_manager.return_value = mock_manager_instance

        result = runner.invoke(brain_app, ["plan", "create", "today"])

        assert result.exit_code == 0
        assert "pending from plan" in result.stdout


class TestPlanHelpers:
    """Tests for plan command helper functions."""

    def test_parse_date_today(self):
        """Test parsing 'today' argument."""
        result = parse_date_arg("today")
        assert result == date.today()

    def test_parse_date_tomorrow(self):
        """Test parsing 'tomorrow' argument."""
        result = parse_date_arg("tomorrow")
        assert result == date.today() + timedelta(days=1)

    def test_parse_date_iso(self):
        """Test parsing ISO date string."""
        result = parse_date_arg("2025-10-12")
        assert result == date(2025, 10, 12)

    def test_extract_tasks_from_empty_diary(self):
        """Test task extraction with empty diary content."""
        mock_llm = Mock()
        tasks = extract_tasks_from_diary("", "2025-10-11", mock_llm)
        assert tasks == []
        # LLM should not be called for empty content
        mock_llm.generate_sync.assert_not_called()

    def test_extract_tasks_from_short_diary(self):
        """Test task extraction with short diary content."""
        mock_llm = Mock()
        tasks = extract_tasks_from_diary("Too short", "2025-10-11", mock_llm)
        assert tasks == []
        # LLM should not be called for short content
        mock_llm.generate_sync.assert_not_called()

    def test_extract_tasks_success(self):
        """Test successful task extraction from diary."""
        mock_llm = Mock()
        mock_llm.generate_sync.return_value = """Here are the tasks:
1. Follow up with Sarah about the project proposal
2. Review pull request #42 before EOD
3. Prepare slides for Thursday presentation
4. Send meeting notes to team"""

        diary_content = "A" * 100  # Substantial content
        tasks = extract_tasks_from_diary(diary_content, "2025-10-11", mock_llm)

        assert len(tasks) == 4
        assert "Follow up with Sarah about the project proposal" in tasks
        assert "Review pull request #42 before EOD" in tasks
        assert "Prepare slides for Thursday presentation" in tasks
        assert "Send meeting notes to team" in tasks
        
        # Verify LLM was called with correct parameters
        mock_llm.generate_sync.assert_called_once()
        call_kwargs = mock_llm.generate_sync.call_args.kwargs
        assert "prompt" in call_kwargs
        assert "system" in call_kwargs
        assert call_kwargs["temperature"] == 0.4
        assert call_kwargs["max_tokens"] == 300

    def test_extract_tasks_no_tasks_found(self):
        """Test task extraction when LLM finds no tasks."""
        mock_llm = Mock()
        mock_llm.generate_sync.return_value = "NO_TASKS"

        diary_content = "A" * 100
        tasks = extract_tasks_from_diary(diary_content, "2025-10-11", mock_llm)

        assert tasks == []

    def test_extract_tasks_with_parentheses_format(self):
        """Test task extraction with parentheses numbering."""
        mock_llm = Mock()
        mock_llm.generate_sync.return_value = """1) First task
2) Second task
3) Third task"""

        diary_content = "A" * 100
        tasks = extract_tasks_from_diary(diary_content, "2025-10-11", mock_llm)

        assert len(tasks) == 3
        assert "First task" in tasks
        assert "Second task" in tasks

    def test_extract_tasks_filters_short_tasks(self):
        """Test that very short tasks are filtered out."""
        mock_llm = Mock()
        mock_llm.generate_sync.return_value = """1. OK
2. This is a proper task description
3. No
4. Another valid task here"""

        diary_content = "A" * 100
        tasks = extract_tasks_from_diary(diary_content, "2025-10-11", mock_llm)

        # Only tasks with >5 characters should be included
        assert len(tasks) == 2
        assert "This is a proper task description" in tasks
        assert "Another valid task here" in tasks

    def test_extract_tasks_handles_llm_error(self):
        """Test task extraction gracefully handles LLM errors."""
        mock_llm = Mock()
        mock_llm.generate_sync.side_effect = Exception("LLM API error")

        diary_content = "A" * 100
        tasks = extract_tasks_from_diary(diary_content, "2025-10-11", mock_llm)

        # Should return empty list on error, not crash
        assert tasks == []


class TestNotesCommands:
    """Tests for notes commands."""

    @patch('brain_cli.notes_commands.get_azure_search_client')
    def test_notes_status_not_configured(self, mock_client):
        """Test notes status when not configured."""
        mock_client.side_effect = ValueError("AZURE_SEARCH_ENDPOINT must be set in .env")

        result = runner.invoke(brain_app, ["notes", "status"])

        assert result.exit_code == 1

    @patch('brain_cli.notes_commands.get_azure_search_client')
    def test_notes_search_not_configured(self, mock_client):
        """Test notes search when not configured."""
        mock_client.side_effect = ValueError("AZURE_SEARCH_ENDPOINT must be set in .env")

        result = runner.invoke(brain_app, ["notes", "search", "test"])

        assert result.exit_code == 1

    @patch('brain_cli.notes_commands.get_azure_search_client')
    def test_notes_status_configured(self, mock_client):
        """Test notes status when configured."""
        mock_search_client = Mock()
        mock_search_client.endpoint = "https://test.search.windows.net"
        mock_search_client.index_name = "test-index"
        mock_search_client.check_connection.return_value = True
        mock_client.return_value = mock_search_client

        result = runner.invoke(brain_app, ["notes", "status"])

        assert result.exit_code == 0
        assert "successful" in result.stdout.lower()



