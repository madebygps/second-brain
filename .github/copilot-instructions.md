# GitHub Copilot Custom Instructions

## Project Overview

AI-powered journaling system with markdown entries, semantic backlinks, and LLM-powered analysis. Integrates with Obsidian or any markdown system. Uses Azure OpenAI for LLM generation.

**Tech Stack:**
- Python 3.13+ with full type hints
- Package manager: `uv` (ALWAYS use `uv`, never `pip`)
- Testing: pytest with 57 tests, 47% coverage
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
- `plan_commands.py` - Daily planning with LLM task extraction (49% coverage)
- `notes_commands.py` - Book notes search (44% coverage)

## Common Commands

```bash
# Planning commands
uv run brain plan create          # Create daily plan with LLM task extraction
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

**Required Paths:**
- `DIARY_PATH` - Path to Obsidian vault or markdown directory (for reflection entries)
- `PLANNER_PATH` - Path to directory for daily plan files (separate from diary)

**Azure OpenAI (required for all LLM features):**
- `AZURE_OPENAI_API_KEY` - API key
- `AZURE_OPENAI_ENDPOINT` - Service endpoint
- `AZURE_OPENAI_DEPLOYMENT` - Model deployment name (e.g., gpt-4o)
- `AZURE_OPENAI_API_VERSION` - Default: 2024-02-15-preview
- ✅ **Full functionality:** Diary prompts, task extraction, semantic analysis, backlinks, tags, reports

**Azure AI Search (required for `brain notes` search only):**
- `AZURE_SEARCH_ENDPOINT` - Search service endpoint
- `AZURE_SEARCH_API_KEY` - API key
- `AZURE_SEARCH_INDEX_NAME` - Index name (default: second-brain-notes)
- ⚠️ **No local alternative:** This is a separate Azure service.

## Entry Structure

Two entry types with specific formats:

**Morning Plan** (YYYY-MM-DD-plan.md):
- Saved to `PLANNER_PATH` (separate from diary)
- Action Items section ONLY
- LLM intelligently extracts actionable tasks from yesterday's diary entry:
  - Identifies incomplete/pending tasks
  - Extracts follow-ups from meetings
  - Filters out completed activities and vague intentions
- Auto-carries forward unchecked todos from yesterday's plan
- All tasks include backlinks to source entries (e.g., "from [[2025-10-14]]")
- Combines both sources (diary + plan) with deduplication
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
- **Linking threshold**: Requires >1 char in Brain Dump section (MIN_SUBSTANTIAL_CONTENT_CHARS = 1)
- **Semantic backlinks**: LLM-powered with confidence scores (high/medium/low)
- **Topic tags**: Emotional/psychological themes, not surface topics
- **Entity extraction**: People, places, projects, themes
- **Task extraction**: LLM analyzes diary entries for actionable tasks (temperature=0.4)
- **File separation**: Plans save to PLANNER_PATH, reflections save to DIARY_PATH
- **88% API call reduction**: Single-pass analysis vs legacy bidirectional

## Module Relationships

```
CLI Layer (brain_cli/)
├── diary_commands.py → report_generator.py, llm_analysis.py
├── plan_commands.py → extract_tasks_from_diary() → LLM
└── notes_commands.py → notes_search_client.py
    ↓
report_generator.py (orchestration)
    ↓ uses
llm_analysis.py (primitives)
    ↓ uses
llm_client.py → azure_openai_client.py
```

**Separation of Concerns:**
- `llm_analysis.py` = Stateless atomic operations (backlinks, tags, entities)
- `report_generator.py` = Stateful orchestration (reports, patterns)
- `plan_commands.py` = Task extraction from diary using LLM
- `entry_manager.py` = I/O and parsing only (supports both diary_path and planner_path)

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
- Removed `generate_planning_prompts()` - plans no longer have prompts
- Total code reduction: ~600 lines

**Module Improvements:**
- Renamed `analysis.py` → `report_generator.py` (clearer purpose)
- Renamed `azure_client.py` → `azure_openai_client.py` (clarity)
- Renamed `azure_search_client.py` → `notes_search_client.py` (clarity)
- Moved plan command from diary to separate `plan_commands.py` module
- Updated `EntryManager` to accept separate diary_path and planner_path

**New Features:**
- LLM-powered task extraction from diary entries (`extract_tasks_from_diary()`)
- Plan entries now save to PLANNER_PATH (separate from diary)
- Combines tasks from both diary analysis and unchecked plan items
- Added TASK_EXTRACTION_TEMPERATURE and TASK_EXTRACTION_MAX_TOKENS constants

**Code Quality:**
- Converted `SemanticLink` to dataclass (type safety)
- Extracted all magic numbers to constants
- Added timing metrics to all LLM operations including task extraction
- Comprehensive docstrings on all helpers
- Maintained 47% test coverage with 57 passing tests
- Added progress spinner for task extraction
