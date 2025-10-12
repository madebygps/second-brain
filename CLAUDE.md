# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"second-brain" is an AI-powered journaling system that creates markdown diary entries with smart prompts, automatic backlinks, and background automation. It integrates with Obsidian (or any markdown-based note system) and uses local LLM via Ollama for intelligent prompting.

- **Python Version**: 3.13+
- **Package Management**: `uv` (ALWAYS use `uv` commands, never `pip` or other package managers)
- **Dependencies**: httpx, python-dotenv, typer, rich, apscheduler, azure-search-documents, openai

## Architecture

The project is organized into two main modules:

### brain_core/ - Business Logic
- `config.py` - Load .env configuration and validate paths (brain_core/config.py:11)
- `entry_manager.py` - Read/write markdown diary entries (brain_core/entry_manager.py:9)
- `ollama_client.py` - Local LLM via HTTP API (brain_core/ollama_client.py:7)
- `azure_client.py` - Azure OpenAI client (brain_core/azure_client.py:7)
- `azure_search_client.py` - Azure AI Search client for book notes (brain_core/azure_search_client.py:20)
- `llm_client.py` - Abstract LLM client interface (brain_core/llm_client.py:7)
- `analysis.py` - Extract themes, statistical analysis (brain_core/analysis.py:7)
- `llm_analysis.py` - LLM-powered semantic backlinks and topic tags (brain_core/llm_analysis.py:7)
- `template_generator.py` - Generate AI prompts from recent entries (brain_core/template_generator.py:5)
- `scheduler.py` - APScheduler for background automation (brain_core/scheduler.py:6)
- `constants.py` - Shared constants (brain_core/constants.py:1)

### brain_cli/ - CLI Interface
- `main.py` - Root CLI entry point with subcommands (brain_cli/main.py:7)
- `diary_commands.py` - Diary management commands (brain_cli/diary_commands.py:26)
- `daemon_commands.py` - Daemon management commands (brain_cli/daemon_commands.py:10)
- `notes_commands.py` - Book notes search via Azure AI Search (brain_cli/notes_commands.py:11)

## Common Commands

```bash
# Diary commands
uv run brain diary create today
uv run brain diary create yesterday
uv run brain diary create 2025-01-15
uv run brain diary link today
uv run brain diary refresh 30
uv run brain diary analyze 30
uv run brain diary todos today
uv run brain diary todos today --save
uv run brain diary list 7
uv run brain diary themes 7

# Daemon commands
uv run brain daemon start
uv run brain daemon stop
uv run brain daemon status

# Notes commands (Azure AI Search)
uv run brain notes search "notes on discipline"
uv run brain notes search "productivity tips" --top 5
uv run brain notes search "deep work" --semantic
uv run brain notes search "learning strategies" --detailed
uv run brain notes status

# Future commands (coming soon):
# uv run brain planner add "task"
```

### Development Commands
```bash
# Install dependencies
uv sync

# Add new dependency
uv add <package-name>

# Add dev dependency
uv add --dev <package-name>
```

## Configuration

Copy `.env.example` to `.env` and configure:

**Required:**
- `DIARY_PATH` - Path to Obsidian vault (or markdown directory)
- `PLANNER_PATH` - Path for extracted todo files

**LLM Provider (choose one):**
- `LLM_PROVIDER` - "ollama" or "azure" (default: ollama)

**Ollama Configuration (when LLM_PROVIDER=ollama):**
- `OLLAMA_MODEL` - Default: llama3.1:latest
- `OLLAMA_URL` - Default: http://localhost:11434

**Azure OpenAI Configuration (when LLM_PROVIDER=azure):**
- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT` - Deployment name (e.g., gpt-4o)
- `AZURE_OPENAI_API_VERSION` - Default: 2024-02-15-preview

**Azure AI Search Configuration (for book notes):**
- `AZURE_SEARCH_ENDPOINT` - Azure Search service endpoint
- `AZURE_SEARCH_API_KEY` - Azure Search API key
- `AZURE_SEARCH_INDEX_NAME` - Index name (default: notes-index)

**Daemon Configuration:**
- `DAEMON_AUTO_LINK_TIME` - Default: 23:00
- `DAEMON_WEEKLY_ANALYSIS` - Default: true
- `DAEMON_REFRESH_DAYS` - Default: 30

## Entry Structure

Each diary entry (YYYY-MM-DD.md) has three sections:

1. **Reflection Prompts** - AI-generated questions based on past 3 days
2. **Brain Dump** - User's free-form writing
3. **Memory Links** - Automatic [[backlinks]] and #tags

## Key Implementation Details

- **Calendar-based context**: Uses past 3 calendar days, not last 3 entries
- **Sunday special**: 5 weekly prompts instead of 3 daily prompts
- **Brain Dump priority**: Only links entries with >50 chars of actual writing
- **LLM-powered linking**: Uses semantic analysis via Ollama to find related entries (diary_core/llm_analysis.py:8)
- **LLM-powered tags**: Generates topic tags based on semantic understanding (diary_core/llm_analysis.py:60)
- **Smart prompts**: Recent entries weighted more heavily in prompt generation

## Daemon Automation

When running, the daemon:
- Auto-links entries at 11pm daily (configurable via DAEMON_AUTO_LINK_TIME)
- Generates weekly analysis every Sunday at 00:05
- Bulk refreshes links every Monday at 02:00
- Runs silently in background with PID stored in ~/.diary-daemon.pid

## Important Notes

- **ALWAYS use `uv` commands** - never use `pip`, `poetry`, `pipenv`, or other package managers
- Requires Ollama running locally with llama3.1:latest model (or configured model)
- Designed for local-first, private journaling (no cloud, no API costs)
- Works best with Obsidian for graph view, mobile sync, and daily notes workflow
