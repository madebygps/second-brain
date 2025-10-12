# Second Brain

AI-powered journaling with smart prompts, semantic backlinks, and background automation.

## Features

- AI-generated reflection prompts with topic diversity
- Semantic backlinks using LLM analysis (not keyword matching)
- Automatic topic tag generation
- Background daemon for daily linking and weekly analysis
- Obsidian-compatible markdown format
- **Flexible LLM**: Local (Ollama) or cloud (Azure OpenAI)

## Quick Start

```bash
# Install dependencies
uv sync

# Configure
cp .env.example .env
# Edit .env with paths and LLM provider

# Option A: Local (Ollama)
ollama pull llama3.1:latest

# Option B: Cloud (Azure OpenAI)
# Set AZURE_OPENAI_* vars in .env

# Create your first entry
uv run diary create today
```

## Usage

```bash
# Entry management
uv run diary create today       # Create entry with AI prompts
uv run diary link today         # Generate semantic backlinks
uv run diary refresh 30         # Bulk refresh past 30 days

# Analysis
uv run diary analyze 30         # Memory trace report
uv run diary themes 7           # Show recurring themes
uv run diary todos today        # Extract action items

# Browsing
uv run diary list 7             # List recent entries

# Background automation
uv run diary-daemon start       # Auto-link at 11pm daily
uv run diary-daemon status      # Check daemon status
```

## Configuration

**Required:**
- `DIARY_PATH` - Your Obsidian vault path
- `PLANNER_PATH` - Path for extracted todos

**Optional:**
- `LLM_PROVIDER` - `ollama` (default) or `azure`

**LLM Options:**
- Ollama: `OLLAMA_MODEL`, `OLLAMA_URL`
- Azure: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`

**Daemon:**
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
- uv package manager
- **Either**: Ollama with llama3.1:latest (local) **or** Azure OpenAI account (cloud)

## License

MIT
