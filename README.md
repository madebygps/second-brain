# Second Brain

AI-powered personal knowledge system with daily planning, reflective journaling, semantic backlinks, and intelligent book notes search.

## Features

**Planning** (`brain plan`)
- LLM extracts actionable tasks from yesterday's diary
- Auto-carries forward unchecked todos from yesterday's plan
- Saves to `PLANNER_PATH` with backlinks to source entries

**Diary** (`brain diary`)
- Evening reflection with AI-generated prompts from past 3 days
- Semantic backlinks via LLM analysis (not keyword matching)
- Automatic topic tags and temporal connections
- Obsidian-compatible markdown format

**Notes Search** (`brain notes`)
- Semantic and text search of book notes via Azure AI Search
- Rich formatted results with highlights

**Cost Tracking** (`brain cost`)
- Real-time Azure OpenAI usage tracking in local SQLite database
- Comprehensive metadata: temperature, max_tokens, prompt/response lengths
- Summaries, trends, projections, and per-operation breakdowns

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

# Cost tracking and analysis
uv run brain cost summary             # Usage summary for last 30 days
uv run brain cost trends 30           # Daily cost trends
uv run brain cost estimate            # Monthly cost projection
uv run brain cost breakdown           # Per-operation breakdown
uv run brain cost export data.json    # Export to JSON
uv run brain cost pricing             # Show pricing

# Logging (Rich-formatted, colored output)
uv run brain --verbose <command>      # Show key operations
uv run brain --debug <command>        # Full diagnostics with LLM details
```

> **Clean UX:** By default, logs are suppressed during operations to avoid interrupting spinners. Use `--verbose` or `--debug` for detailed information with beautiful Rich formatting.

> **Cost Tracking:** All Azure OpenAI usage is automatically tracked in a local SQLite database (`~/.brain/costs.db`). Data stays private and grows ~10-50 MB/year for typical use.

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

**Cost Tracking** (optional configuration):
- `BRAIN_COST_DB_PATH` - Path to cost tracking database (default: ~/.brain/costs.db)
- `BRAIN_LOG_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `BRAIN_LOG_FILE` - Path to log file (optional, logs to console if not set)

**Custom Pricing** (optional - override Azure OpenAI pricing):
- `AZURE_GPT4O_INPUT_PRICE` - Price per 1K input tokens for gpt-4o (default: 0.03)
- `AZURE_GPT4O_OUTPUT_PRICE` - Price per 1K output tokens for gpt-4o (default: 0.06)
- `AZURE_GPT4O_MINI_INPUT_PRICE` - Price per 1K input tokens for gpt-4o-mini (default: 0.0015)
- `AZURE_GPT4O_MINI_OUTPUT_PRICE` - Price per 1K output tokens for gpt-4o-mini (default: 0.006)
- `AZURE_GPT4_INPUT_PRICE` - Price per 1K input tokens for gpt-4 (default: 0.03)
- `AZURE_GPT4_OUTPUT_PRICE` - Price per 1K output tokens for gpt-4 (default: 0.06)
- `AZURE_GPT35_TURBO_INPUT_PRICE` - Price per 1K input tokens for gpt-35-turbo (default: 0.0015)
- `AZURE_GPT35_TURBO_OUTPUT_PRICE` - Price per 1K output tokens for gpt-35-turbo (default: 0.002)

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

Minimal test suite focused on preventing data loss:

```bash
uv run pytest                    # Run all tests
uv run pytest --cov              # Run with coverage
```

**Coverage**: 7 essential tests covering:
- Configuration validation (missing paths)
- File naming (reflection vs. plan entries)
- Write/read cycles (prevent data loss)
- Path separation (diary vs. planner)

## License

MIT
