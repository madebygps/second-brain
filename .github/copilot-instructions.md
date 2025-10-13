# GitHub Copilot Custom Instructions

## Project Overview

AI-powered journaling system with markdown entries, semantic backlinks, and LLM-powered analysis. Integrates with Obsidian or any markdown system. Uses Azure OpenAI for LLM generation.

**Tech Stack:**
- Python 3.13+ with full type hints
- Package manager: `uv` (ALWAYS use `uv`, never `pip`)
- Testing: pytest with 64 tests, 50% coverage
- CLI: typer (add_completion=False) + rich
- LLM: Azure OpenAI (required)
- Search: Azure AI Search for book notes

## Architecture

Two main modules with clear separation:

### brain_core/ - Business Logic
Core functionality with comprehensive type hints and dataclasses:

- `config.py` - Configuration management (91% coverage)
- `constants.py` - Shared constants (100% coverage)
- `entry_manager.py` - Entry I/O and parsing (93% coverage)
- `llm_client.py` - Abstract LLM interface (73% coverage)
- `azure_openai_client.py` - Azure OpenAI client (40% coverage)
- `notes_search_client.py` - Book notes search (100% coverage)
- `llm_analysis.py` - Atomic LLM operations: entities, backlinks, tags (17% coverage)
- `report_generator.py` - Report orchestration (18% coverage)
- `template_generator.py` - AI prompt generation (42% coverage)

### brain_cli/ - CLI Interface
User-facing commands with typer:

- `main.py` - Root CLI entry point (92% coverage)
- `diary_commands.py` - Diary management (23% coverage)
- `plan_commands.py` - Daily planning (73% coverage)
- `notes_commands.py` - Book notes search (44% coverage)

## Common Commands

```bash
# Planning commands
uv run brain plan create          # Create daily plan (auto-carries todos)
uv run brain plan create tomorrow # Plan for tomorrow

# Diary commands
uv run brain diary create         # Create evening reflection entry
uv run brain diary link           # Generate semantic backlinks + tags
uv run brain diary report 7       # Memory trace analysis for 7 days
uv run brain diary patterns 7     # Statistical patterns
uv run brain diary list           # List all entries
uv run brain diary refresh 30     # Regenerate links for last 30 days

# Notes commands (Azure AI Search)
uv run brain notes search "topic"
uv run brain notes search "query" --top 5
uv run brain notes search "query" --semantic
uv run brain notes search "query" --detailed
uv run brain notes status

# Development
uv sync                           # Install dependencies
uv add <package>                  # Add dependency
uv add --dev <package>            # Add dev dependency
uv run pytest tests/ -v           # Run tests
uv run pytest tests/ --cov        # With coverage
```

## Configuration (.env)

**Required:**
- `DIARY_PATH` - Path to Obsidian vault or markdown directory
- `PLANNER_PATH` - Path for extracted todo files

**Azure OpenAI (required):**
- `AZURE_OPENAI_API_KEY` - API key
- `AZURE_OPENAI_ENDPOINT` - Service endpoint
- `AZURE_OPENAI_DEPLOYMENT` - Model deployment name (e.g., gpt-4o)
- `AZURE_OPENAI_API_VERSION` - Default: 2024-02-15-preview
- ✅ **Full functionality:** Supports both `brain diary` and `brain notes` commands.

**Azure AI Search (required for `brain notes` search):**
- `AZURE_SEARCH_ENDPOINT` - Search service endpoint
- `AZURE_SEARCH_API_KEY` - API key
- `AZURE_SEARCH_INDEX_NAME` - Index name (default: notes-index)
- ⚠️ **No local alternative:** This is a separate Azure service.

## Entry Structure

Two entry types with specific formats:

**Morning Plan** (YYYY-MM-DD-plan.md):
- Action Items section ONLY
- LLM intelligently extracts actionable tasks from yesterday's diary entry
- Auto-carries forward unchecked todos from yesterday's plan
- All tasks include backlinks to source entries
- Simple, distraction-free format for task management

**Evening Reflection** (YYYY-MM-DD.md):
- Reflection Prompts (AI-generated from past 3 calendar days)
- Brain Dump section (main content)
- Memory Links section (automatic [[backlinks]] and #tags)

**Sunday Special**: 5 weekly prompts instead of 3 daily prompts

## Code Patterns & Best Practices

### Type Safety
- Full type hints on all functions (Python 3.13+)
- Use `Literal` for string enums (e.g., `ConfidenceLevel = Literal["high", "medium", "low"]`)
- Dataclasses for structured data (e.g., `SemanticLink`, `DiaryEntry`)
- Type aliases for clarity

### Error Handling
- Specific exceptions (RuntimeError for LLM failures, ValueError for validation)
- Comprehensive logging with context
- Graceful degradation (return empty results, not crashes)

### LLM Calls
- Always use named parameters: `prompt=`, `system=`, `temperature=`, `max_tokens=`
- Add timing metrics: `start_time = time.time()` → log `elapsed`
- Clean JSON responses with `_clean_json_response()`
- Truncate text to manage token costs

### Testing
- Use pytest with fixtures in `tests/conftest.py`
- Mock environment variables with `monkeypatch`
- Integration tests via CLI commands preferred
- Run with: `uv run pytest tests/ -v`

### Constants
- All magic numbers in `brain_core/constants.py`
- Import specific constants needed
- Never hardcode values like lengths, thresholds, temperatures

### Logging
- Use module-level logger: `logger = logging.getLogger(__name__)`
- Include timing info: `f"Operation completed in {elapsed:.2f}s"`
- Add context: entry dates, counts, operation details

## Key Implementation Details

- **Calendar-based context**: Uses past 3 calendar days, not last 3 entries
- **Linking threshold**: Requires >50 chars in Brain Dump section
- **Semantic backlinks**: LLM-powered with confidence scores (high/medium/low)
- **Topic tags**: Emotional/psychological themes, not surface topics
- **Entity extraction**: People, places, projects, themes
- **88% API call reduction**: Single-pass analysis vs legacy bidirectional

## Module Relationships

```
CLI Layer (brain_cli/)
    ↓
report_generator.py (orchestration)
    ↓ uses
llm_analysis.py (primitives)
    ↓ uses
llm_client.py → azure_openai_client.py
```

**Separation of Concerns:**
- `llm_analysis.py` = Stateless atomic operations
- `report_generator.py` = Stateful orchestration
- `entry_manager.py` = I/O and parsing only

## Important Notes

- **ALWAYS use `uv`** for package management (never `pip`)
- **Type hints required** on all new functions
- **Extract constants** - no magic numbers in code
- **Add timing metrics** to LLM operations
- **Log with context** - include entry dates, counts
- **Named parameters** for LLM calls
- **Validate inputs** - check empty lists, None values
- **Test coverage** - aim for 60%+ on new code
- Requires Azure OpenAI configured
- Local-first, private journaling system
- Best used with Obsidian for graph view and mobile sync

## Recent Refactoring

**Architecture Simplification:**
- Removed Ollama client (195 lines) - Azure OpenAI only
- Removed scheduler/daemon system (312 lines, 0% coverage)
- Removed todos command (redundant with plan command)
- Total code reduction: ~500 lines

**Module Improvements:**
- Renamed `analysis.py` → `report_generator.py` (clearer purpose)
- Renamed `azure_client.py` → `azure_openai_client.py` (clarity)
- Renamed `azure_search_client.py` → `notes_search_client.py` (clarity)
- Moved `extract_todos()` to `entry_manager.py` (better organization)

**Code Quality:**
- Converted `SemanticLink` to dataclass (type safety)
- Extracted all magic numbers to constants
- Added 4 helper functions for DRY principle (2 in diary, 2 in notes)
- Added timing metrics to all LLM operations
- Comprehensive docstrings on all helpers
- Fixed 4 critical bugs in diary_commands
- Improved from 47% → 50% test coverage
