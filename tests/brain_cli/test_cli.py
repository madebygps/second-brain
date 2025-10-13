"""Integration tests for CLI commands."""
import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from brain_cli.main import app as brain_app


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
        assert 'plan' in result.stdout
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

    @patch('brain_cli.diary_commands.get_config')
    @patch('brain_cli.diary_commands.get_llm_client')
    @patch('brain_cli.diary_commands.EntryManager')
    @patch('brain_cli.diary_commands.generate_planning_prompts')
    def test_diary_plan_command(self, mock_gen_prompts, mock_manager, mock_llm, mock_config, mock_env):
        """Test diary plan command."""
        # Setup mocks
        mock_config.return_value = Mock(
            diary_path=mock_env["diary_path"]
        )
        mock_llm_instance = Mock()
        mock_llm_instance.check_connection_sync.return_value = True
        mock_llm.return_value = mock_llm_instance

        mock_manager_instance = Mock()
        mock_manager_instance.entry_exists.return_value = False
        mock_manager_instance.read_entry.return_value = None
        mock_manager_instance.create_plan_template.return_value = Mock(
            filename="2025-10-12-plan.md",
            date=Mock(isoformat=lambda: "2025-10-12")
        )
        mock_manager.return_value = mock_manager_instance

        mock_gen_prompts.return_value = [
            "What are your priorities?",
            "What needs preparation?",
            "What unfinished items?"
        ]

        result = runner.invoke(brain_app, ["diary", "plan", "2025-10-12"])

        assert result.exit_code == 0
        assert "Created plan entry" in result.stdout or "2025-10-12-plan.md" in result.stdout

    @patch('brain_cli.diary_commands.get_config')
    @patch('brain_cli.diary_commands.EntryManager')
    def test_diary_plan_already_exists(self, mock_manager, mock_config, mock_env):
        """Test diary plan command when entry already exists."""
        mock_config.return_value = Mock(
            diary_path=mock_env["diary_path"]
        )

        mock_manager_instance = Mock()
        mock_manager_instance.entry_exists.return_value = True
        mock_manager.return_value = mock_manager_instance

        result = runner.invoke(brain_app, ["diary", "plan", "2025-10-12"])

        assert "already exists" in result.stdout.lower()


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



