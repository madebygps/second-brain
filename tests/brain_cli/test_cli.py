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
        assert "daemon" in result.stdout.lower()
        assert "notes" in result.stdout.lower()

    def test_diary_subcommand_help(self):
        """Test brain diary --help command."""
        result = runner.invoke(brain_app, ["diary", "--help"])
        assert result.exit_code == 0
        assert "create" in result.stdout.lower()
        assert "link" in result.stdout.lower()
        assert "analyze" in result.stdout.lower()

    def test_daemon_subcommand_help(self):
        """Test brain daemon --help command."""
        result = runner.invoke(brain_app, ["daemon", "--help"])
        assert result.exit_code == 0
        assert "start" in result.stdout.lower()
        assert "stop" in result.stdout.lower()
        assert "status" in result.stdout.lower()

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
            diary_path=mock_env["diary_path"],
            llm_provider="ollama"
        )
        mock_manager.return_value.list_entries.return_value = []

        result = runner.invoke(brain_app, ["diary", "list", "7"])

        # Should run without error even with no entries
        assert "No entries found" in result.stdout or result.exit_code == 0

    @patch('brain_cli.diary_commands.get_config')
    @patch('brain_cli.diary_commands.get_llm_client')
    @patch('brain_cli.diary_commands.EntryManager')
    def test_diary_themes_command(self, mock_manager, mock_llm, mock_config, mock_env):
        """Test diary themes command."""
        mock_config.return_value = Mock(
            diary_path=mock_env["diary_path"],
            llm_provider="ollama"
        )
        mock_manager.return_value.list_entries.return_value = []

        result = runner.invoke(brain_app, ["diary", "themes", "7"])

        assert "No entries found" in result.stdout or result.exit_code == 0


class TestNotesCommands:
    """Tests for notes commands."""

    @patch('brain_cli.notes_commands.get_azure_search_client')
    def test_notes_status_not_configured(self, mock_client):
        """Test notes status when not configured."""
        mock_client.return_value = None

        result = runner.invoke(brain_app, ["notes", "status"])

        assert result.exit_code == 1
        assert "not configured" in result.stdout.lower()

    @patch('brain_cli.notes_commands.get_azure_search_client')
    def test_notes_search_not_configured(self, mock_client):
        """Test notes search when not configured."""
        mock_client.return_value = None

        result = runner.invoke(brain_app, ["notes", "search", "test"])

        assert result.exit_code == 1
        assert "not configured" in result.stdout.lower()

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


class TestDaemonCommands:
    """Tests for daemon commands."""

    @patch('brain_cli.daemon_commands.PIDFILE')
    def test_daemon_status_not_running(self, mock_pidfile):
        """Test daemon status when not running."""
        mock_pidfile.exists.return_value = False

        result = runner.invoke(brain_app, ["daemon", "status"])

        assert "not running" in result.stdout.lower()
