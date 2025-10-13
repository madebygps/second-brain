# Second Brain

AI-powered journaling with semantic backlinks and intelligent book notes search.

## Features

**Diary:**
- **Morning planning entries** - Forward-looking prompts based on yesterday's reflections
- **Evening reflection entries** - AI-generated prompts with topic diversity
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

# Morning: Create your planning entry
uv run brain diary plan today

# Evening: Create your reflection entry
uv run brain diary create today

# Search your book notes
uv run brain notes search "discipline"
```

## Usage

```bash
# Diary management
uv run brain diary plan today         # Morning: Create planning entry
uv run brain diary plan tomorrow      # Plan for tomorrow
uv run brain diary create today       # Evening: Create reflection entry
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

**Required:**
- `DIARY_PATH` - Path to Obsidian vault or markdown directory
- `PLANNER_PATH` - Path for extracted plan files
- `AZURE_SEARCH_ENDPOINT` - Azure AI Search service endpoint
- `AZURE_SEARCH_API_KEY` - Azure AI Search API key
- `AZURE_SEARCH_INDEX_NAME` - Search index name (default: `notes-index`)

**Azure OpenAI** (required):
- `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint
- `AZURE_OPENAI_DEPLOYMENT` - Deployment name (default: gpt-4o)
- `AZURE_OPENAI_API_VERSION` - API version (default: 2024-02-15-preview)

## Entry Format

**Morning Plan Entry** (`YYYY-MM-DD-plan.md`):

```markdown
## Daily Focus
**1. Based on [[2025-01-14]], how will you follow up on X?**
**2. What meetings need preparation today?**
**3. What are your main priorities?**

---

## Action Items
- [ ] Task from yesterday (from [[2025-01-14]])
- [ ] New task

---

## Brain Dump
Your planning thoughts...
```

**Evening Reflection Entry** (`YYYY-MM-DD.md`):

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
- uv package manager
- **Azure OpenAI** - Required for all LLM operations (diary prompts, analysis, backlinks)
- **Azure AI Search** - Required for book notes search functionality

## Testing

```bash
uv run pytest                    # Run all tests
uv run pytest --cov              # Run with coverage
uv run pytest tests/brain_core/  # Run specific module
```

## License

MIT
