# Second Brain

AI-powered journaling with semantic backlinks and intelligent book notes search.

## Features

**Planning:**
- Daily task management with action items
- LLM-powered task extraction from yesterday's diary entry
- Auto-carries forward unchecked todos from yesterday's plan
- Simple, distraction-free format

**Diary:**
- Evening reflection entries with AI-generated prompts
- Semantic backlinks using LLM analysis (not keyword matching)
- Automatic topic tag generation
- Bulk refresh command for regenerating links
- Obsidian-compatible markdown format

**Notes Search:**
- Search book notes via Azure AI Search
- Semantic and text search modes
- Rich formatted results
- **Requires Azure AI Search** (no local alternative)

**LLM Support:**
- Azure OpenAI - Full functionality for all commands

## Quick Start

```bash
# Install dependencies
uv sync

# Configure
cp .env.example .env
# Edit .env with your paths and Azure credentials

# Morning: Create your planning entry (saves to PLANNER_PATH)
uv run brain plan create today

# Evening: Create your reflection entry (saves to DIARY_PATH)
uv run brain diary create today

# Search your book notes
uv run brain notes search "discipline"
```

## Usage

```bash
# Planning
uv run brain plan create today        # Create daily plan with LLM task extraction
uv run brain plan create tomorrow     # Plan for tomorrow

# Diary management
uv run brain diary create today       # Create reflection entry
uv run brain diary link today         # Generate semantic backlinks
uv run brain diary refresh 30         # Bulk refresh past 30 days
uv run brain diary list 7             # List recent entries

# Analysis
uv run brain diary report 30          # Memory trace report (activities & connections)
uv run brain diary patterns 7         # Emotional & psychological patterns

# Notes search
uv run brain notes search "topic"     # Search book notes
uv run brain notes search "topic" --semantic --detailed
uv run brain notes status             # Check connection


```

## Configuration

**Required Paths:**
- `DIARY_PATH` - Path to Obsidian vault or markdown directory for reflection entries
- `PLANNER_PATH` - Path to directory for daily plan files (separate from diary)

**Azure OpenAI** (required for all LLM features):
- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT` - Deployment name (default: gpt-4o)
- `AZURE_OPENAI_API_VERSION` - API version (default: 2024-02-15-preview)

**Azure AI Search** (required for notes search):
- `AZURE_SEARCH_ENDPOINT` - Azure AI Search service endpoint
- `AZURE_SEARCH_API_KEY` - Azure AI Search API key
- `AZURE_SEARCH_INDEX_NAME` - Search index name (default: second-brain-notes)

## Entry Format

**Morning Plan Entry** (`YYYY-MM-DD-plan.md`):

Saved to `PLANNER_PATH`. Created with `brain plan create`, which intelligently:
- Extracts actionable tasks from yesterday's diary using LLM
- Carries forward unchecked todos from yesterday's plan
- Adds backlinks to source entries

```markdown
## Action Items
- [ ] Follow up with team about project (from [[2025-01-14]])
- [ ] Review pull requests (from [[2025-01-14]])
- [ ] Uncompleted task from yesterday (from [[2025-01-14]])
```

**Evening Reflection Entry** (`YYYY-MM-DD.md`):

Saved to `DIARY_PATH`. Created with `brain diary create`:

```markdown
## Reflection Prompts
**1. Based on [[2025-01-14]], how did X work out?**

---

## Brain Dump
Your reflections...
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
- uv package manager (ALWAYS use `uv`, never `pip`)
- **Azure OpenAI** - Required for all LLM operations:
  - Diary prompt generation
  - Task extraction from diary entries
  - Semantic backlinks and tags
  - Analysis reports and patterns
- **Azure AI Search** - Required for book notes search functionality only

## Testing

```bash
uv run pytest                    # Run all tests
uv run pytest --cov              # Run with coverage
uv run pytest tests/brain_core/  # Run specific module
```

## License

MIT
