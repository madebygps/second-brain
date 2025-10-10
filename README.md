# Second Brain

AI-powered journaling with smart prompts, semantic backlinks, and background automation.

## Features

- AI-generated reflection prompts based on your past entries
- Semantic backlinks using LLM analysis (not just keyword matching)
- Automatic topic tag generation
- Background daemon for daily linking and weekly analysis
- Obsidian-compatible markdown format
- Fully local with Ollama (no cloud, no API costs)

## Quick Start

```bash
# Install dependencies
uv sync

# Configure paths
cp .env.example .env
# Edit .env with DIARY_PATH and PLANNER_PATH

# Install Ollama and pull model
ollama pull llama3.1:latest

# Install CLI globally (optional)
uv tool install .

# Create your first entry
diary create today
```

## Usage

```bash
# Entry management
diary create today              # Create entry with AI prompts
diary link today                # Generate semantic backlinks
diary refresh 30                # Bulk refresh past 30 days

# Analysis
diary analyze 30                # Memory trace report
diary themes 7                  # Show recurring themes
diary todos today               # Extract action items

# Browsing
diary list 7                    # List recent entries

# Background automation
diary-daemon start              # Auto-link at 11pm daily
diary-daemon status             # Check daemon status
```

## Configuration

Required in `.env`:
- `DIARY_PATH` - Path to your Obsidian vault
- `PLANNER_PATH` - Path for extracted todos

Optional:
- `OLLAMA_MODEL` - Default: llama3.1:latest
- `OLLAMA_URL` - Default: http://localhost:11434
- `DAEMON_AUTO_LINK_TIME` - Default: 23:00
- `DAEMON_WEEKLY_ANALYSIS` - Default: true

## Entry Format

Created entries have two sections:

```markdown
## Reflection Prompts
**1. Based on [[2025-01-14]], how did X work out?**

---

## Brain Dump
Your writing here...
```

After writing, run `diary link today` to add semantic backlinks:

```markdown
---

## Memory Links
**Temporal:** [[2025-01-14]] • [[2025-01-13]]
**Topics:** #focus #energy
```

## Requirements

- Python 3.13+
- Ollama with llama3.1:latest
- uv package manager

## License

MIT
