# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"second-brain" is an AI-powered journaling system that creates markdown diary entries with smart prompts, automatic backlinks, and background automation. It integrates with Obsidian (or any markdown-based note system) and uses local LLM via Ollama for intelligent prompting.

- **Python Version**: 3.13+
- **Package Management**: `uv` (ALWAYS use `uv` commands, never `pip` or other package managers)
- **Dependencies**: httpx, python-dotenv, typer, rich, apscheduler

## Architecture

The project is organized into three main modules:

### diary_core/ - Business Logic
- `config.py` - Load .env configuration and validate paths (diary_core/config.py:11)
- `entry_manager.py` - Read/write markdown diary entries (diary_core/entry_manager.py:9)
- `ollama_client.py` - Local LLM via HTTP API (diary_core/ollama_client.py:7)
- `analysis.py` - Extract themes, statistical analysis (diary_core/analysis.py:7)
- `llm_analysis.py` - LLM-powered semantic backlinks and topic tags (diary_core/llm_analysis.py:7)
- `template_generator.py` - Generate AI prompts from recent entries (diary_core/template_generator.py:5)

### diary_cli/ - Manual Commands
- `main.py` - CLI interface using Typer (diary_cli/main.py:13)

### diary_daemon/ - Background Automation
- `scheduler.py` - APScheduler for automated tasks (diary_daemon/scheduler.py:6)
- `main.py` - Daemon management CLI (diary_daemon/main.py:6)

## Common Commands

### Diary CLI Commands
```bash
# Create new entry with AI-generated prompts
uv run diary create today
uv run diary create yesterday
uv run diary create 2025-01-15

# Generate backlinks and tags for entry
uv run diary link today

# Bulk refresh backlinks for all entries
uv run diary refresh 30

# Generate memory trace analysis
uv run diary analyze 30

# Extract action items/todos
uv run diary todos today
uv run diary todos today --save  # Save to planner

# List recent entries
uv run diary list 7

# Show recurring themes
uv run diary themes 7
```

### Daemon Commands
```bash
# Start background daemon
uv run diary-daemon start

# Stop daemon
uv run diary-daemon stop

# Check daemon status
uv run diary-daemon status
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

**Optional:**
- `OLLAMA_MODEL` - Default: llama3.1:latest
- `OLLAMA_URL` - Default: http://localhost:11434
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
