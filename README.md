# Second Brain

AI-powered journaling that creates markdown diary entries with smart prompts, automatic backlinks, and background automation.

## Features

- **AI-Generated Prompts**: Get contextual reflection questions based on your past 3 days
- **Semantic Backlinks**: LLM finds related entries based on meaning, not just keywords
- **Smart Topic Tags**: LLM generates meaningful tags from semantic understanding
- **Background Automation**: Daemon handles linking and weekly analysis
- **Obsidian Integration**: Works seamlessly with Obsidian vaults
- **Local & Private**: Uses local LLM via Ollama (no cloud, no API costs)

## Quick Start

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your paths
   ```

3. **Install Ollama** (if not already installed):
   - Download from [ollama.com](https://ollama.com)
   - Pull the model: `ollama pull llama3.1:latest`

4. **Install the CLI globally** (optional but recommended):
   ```bash
   uv tool install .
   ```

   Now you can use `diary` and `diary-daemon` directly without `uv run`:
   ```bash
   diary create today
   diary-daemon start
   ```

   Alternatively, activate the virtual environment:
   ```bash
   source .venv/bin/activate
   diary create today
   ```

## Daily Workflow

### Morning
```bash
diary create today
```
Opens your Obsidian vault with AI-generated reflection prompts based on your recent entries.

### Throughout the Day
Write freely in the "Brain Dump" section of your entry in Obsidian.

### Evening (Manual)
```bash
diary link today
```
Or let the daemon handle it automatically at 11pm.

### Weekly Analysis
Every Sunday, the daemon generates a memory trace report showing themes and connections.

## CLI Commands

> **Note**: Commands below assume you've installed globally with `uv tool install .` or activated the virtual environment. Otherwise, prefix commands with `uv run`.

```bash
# Entry management
diary create today              # Create entry with AI prompts
diary create yesterday          # Create yesterday's entry
diary create 2025-01-15         # Create specific date

# Linking and analysis
diary link today                # Generate backlinks and tags for single entry
diary refresh 30                # Bulk refresh backlinks for all entries (past 30 days)
diary analyze 30                # Memory trace report (30 days)

# Todo extraction
diary todos today               # Extract action items
diary todos today --save        # Save to planner file

# Browsing
diary list 7                    # List recent entries
diary themes 7                  # Show recurring themes

# Background daemon
diary-daemon start              # Start daemon
diary-daemon stop               # Stop daemon
diary-daemon status             # Check status
```

## Configuration

Edit `.env` with your settings:

**Required**:
- `DIARY_PATH` - Path to your Obsidian vault
- `PLANNER_PATH` - Path for extracted todo files

**Optional**:
- `OLLAMA_MODEL` - LLM model (default: llama3.1:latest)
- `OLLAMA_URL` - Ollama API URL (default: http://localhost:11434)
- `DAEMON_AUTO_LINK_TIME` - Auto-link time (default: 23:00)
- `DAEMON_WEEKLY_ANALYSIS` - Enable weekly reports (default: true)
- `DAEMON_REFRESH_DAYS` - Days to refresh in bulk (default: 30)

## Entry Structure

Each entry (`YYYY-MM-DD.md`) contains:

```markdown
## Reflection Prompts
**1. Based on [[2025-01-14]], how did X work out?**
**2. What are you thinking about today?**
**3. How are you feeling about Y?**

---

## Brain Dump
[Your writing here...]

---

## Memory Links
**Temporal:** [[2025-01-14]] • [[2025-01-13]]
**Topics:** #focus #energy
```

## Architecture

- **diary_core/** - Business logic (entry management, analysis, LLM client)
- **diary_cli/** - Manual CLI commands
- **diary_daemon/** - Background automation

## Requirements

- Python 3.13+
- Ollama with llama3.1:latest
- Obsidian (recommended) or any markdown editor

## License

MIT
