# Second Brain

AI-powered second brain with intelligent journaling, book notes search, and background automation.

## Features

**Diary:**
- AI-generated reflection prompts with topic diversity
- Semantic backlinks using LLM analysis (not keyword matching)
- Automatic topic tag generation
- Background daemon for daily linking and weekly analysis
- Obsidian-compatible markdown format

**Notes Search:**
- Search book notes via Azure AI Search
- Semantic and text search modes
- Rich formatted results

**LLM Support:**
- Local (Ollama) or cloud (Azure OpenAI)

## Quick Start

```bash
# Install dependencies
uv sync

# Configure
cp .env.example .env
# Edit .env with your paths and credentials

# Create your first diary entry
uv run brain diary create today

# Search your book notes (requires Azure AI Search)
uv run brain notes search "discipline"
```

## Usage

```bash
# Diary management
uv run brain diary create today       # Create entry with AI prompts
uv run brain diary link today         # Generate semantic backlinks
uv run brain diary refresh 30         # Bulk refresh past 30 days
uv run brain diary list 7             # List recent entries

# Analysis
uv run brain diary analyze 30         # Memory trace report
uv run brain diary themes 7           # Show recurring themes
uv run brain diary todos today        # Extract action items

# Notes search
uv run brain notes search "topic"     # Search book notes
uv run brain notes search "topic" --semantic --detailed
uv run brain notes status             # Check connection

# Background automation
uv run brain daemon start             # Auto-link at 11pm daily
uv run brain daemon status            # Check daemon status
```

## Configuration

**Required:**
- `DIARY_PATH` - Obsidian vault path
- `PLANNER_PATH` - Path for extracted todos

**LLM Provider** (choose one):
- `LLM_PROVIDER=ollama` → `OLLAMA_MODEL`, `OLLAMA_URL`
- `LLM_PROVIDER=azure` → `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT`

**Notes Search** (optional):
- `AZURE_SEARCH_ENDPOINT`, `AZURE_SEARCH_API_KEY`, `AZURE_SEARCH_INDEX_NAME`

**Daemon** (optional):
- `DAEMON_AUTO_LINK_TIME` (default: 23:00)
- `DAEMON_WEEKLY_ANALYSIS` (default: true)

## Entry Format

Created entries have two sections:

```markdown
## Reflection Prompts
**1. Based on [[2025-01-14]], how did X work out?**

---

## Brain Dump
Your writing here...
```

After writing, run `brain diary link today` to add semantic backlinks:

```markdown
---

## Memory Links
**Temporal:** [[2025-01-14]] • [[2025-01-13]]
**Topics:** #focus #energy
```

## Requirements

- Python 3.13+
- uv package manager
- LLM: Ollama (local) or Azure OpenAI (cloud)
- Optional: Azure AI Search (for notes search)

## Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov

# Run specific test file
uv run pytest tests/brain_core/test_azure_search_client.py
```

**Current coverage:** 23% (18 passing tests)

## License

MIT
