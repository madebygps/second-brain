# Design Philosophy

## Core Principles

### 1. Local-First, Privacy by Default

Your thoughts are yours alone:
- All entries stored as plain markdown on your machine
- No cloud sync unless you choose (Obsidian Sync, iCloud, etc.)
- Ollama support for 100% local LLM processing
- Cost tracking database stays local (`~/.brain/costs.db`)

### 2. Semantic Over Syntactic

Traditional journaling relies on keyword matching and manual tagging. Second Brain uses LLM-powered semantic understanding:

**Traditional approach:**
```markdown
Mentioned "project" → finds all entries with "project"
```

**Semantic approach:**
```markdown
"Feeling stuck on the redesign" → links to "Made progress on UI overhaul"
(Even though they use different words, the LLM understands the connection)
```

### 3. Reflection, Not Recording

The system is designed for **reflective journaling**, not life logging:

**Evening Reflection (`YYYY-MM-DD.md`):**
- How did today feel?
- What patterns am I noticing?
- What's on my mind?

**Not designed for:**
- Timestamped logs ("8am: breakfast, 9am: meeting")
- Detailed task tracking (use a proper task manager)
- Meeting notes (use Obsidian daily notes or similar)

### 4. Separation of Planning and Reflection

Two distinct mental modes with separate file locations:

**Morning Planning** (`PLANNER_PATH`):
- Future-focused: What needs to happen today?
- Action-oriented: Concrete todos with checkboxes
- Intelligently extracted from yesterday's reflections

**Evening Reflection** (`DIARY_PATH`):
- Past-focused: What actually happened?
- Emotional/psychological processing
- Free-form brain dump without structure constraints

This separation prevents:
- Task lists cluttering reflective space
- Reflection entries getting lost among todos
- Mental mode confusion (doing vs. being)

### 5. AI as Assistant, Not Replacement

LLMs enhance but don't replace human insight:

**LLM handles:**
- Pattern recognition across entries
- Suggesting semantic connections
- Extracting actionable items from prose
- Identifying emotional themes

**You provide:**
- Original thoughts and reflections
- Judgment on which connections matter
- Context that LLMs can't infer
- The actual journaling habit

### 6. Minimal Viable Tracking

The system intentionally lacks:
- ❌ Habit tracking (use Habitica, Streaks, etc.)
- ❌ Goal management (use OKR tools)
- ❌ Time tracking (use Toggl, RescueTime, etc.)
- ❌ Project management (use Linear, Asana, etc.)

Instead, it focuses on:
- ✅ Daily reflection prompts from your own past
- ✅ Semantic connections between thoughts over time
- ✅ Extracting actionable next steps
- ✅ Psychological/emotional pattern analysis

### 7. Obsidian-Compatible, Not Obsidian-Dependent

The system produces standard markdown:
- Works great with Obsidian (graph view, mobile sync)
- Also works with any markdown editor
- No proprietary formats or lock-in
- Plain text = future-proof

## Entry Philosophy

### Morning Plans: Task Extraction Intelligence

When you run `brain plan create today`, the LLM analyzes yesterday's diary entry with specific criteria:

**Extracts:**
- ✅ Incomplete tasks ("still need to...")
- ✅ Follow-ups from meetings ("will reach out tomorrow")
- ✅ Intentions with specific objects ("want to review the PR")
- ✅ Blockers that need action ("waiting for response from...")

**Filters out:**
- ❌ Completed activities ("finished the report")
- ❌ Vague intentions ("should be more productive")
- ❌ Emotional reflections ("feeling overwhelmed")
- ❌ Social activities without clear next steps ("had coffee with Alex")

The LLM uses `temperature=0.4` for balanced creativity and consistency.

### Evening Reflections: Semantic Linking

When you run `brain diary link today`, the system:

1. **Analyzes content** (not keywords):
   - Extracts people, places, projects, themes
   - Understands emotional context
   - Identifies psychological patterns

2. **Suggests connections** with confidence scores:
   - `high`: Strong thematic overlap, clear relationship
   - `medium`: Potential connection worth exploring
   - `low`: Weak signal, may be coincidental

3. **Generates psychological tags** (not topic tags):
   - ✅ `#perfectionism` `#self-doubt` `#growth`
   - ❌ `#work` `#gym` `#coffee`

The system looks for **emotional** and **psychological** themes, not surface-level topics.

### Temporal Context: Calendar-Based, Not Entry-Based

Prompts and analysis use **calendar days**, not "last 3 entries":

**Why?**
- Skipping journaling shouldn't break context
- Weekend gaps are natural and expected
- Calendar rhythm matches human memory

**Example:**
- Today: October 15
- Context: October 14, 13, 12 (even if you skipped Oct 13)

**Sunday Special:**
- Gets 5 weekly prompts instead of 3 daily prompts
- Encourages bigger-picture reflection

## Analysis Philosophy

### Memory Trace Reports

`brain diary report <days>` generates a narrative summary:
- Key activities and events
- Emotional patterns across timespan
- Semantic connections between entries
- Entity frequency (people, places, projects)

**Purpose:** Help you see the forest, not just trees.

### Pattern Analysis

`brain diary patterns <days>` identifies emotional/psychological themes:
- Ranked by frequency
- Pure psychological tags (no surface topics)
- Helps spot recurring mental patterns

**Example output:**
```
1. #self-doubt
2. #perfectionism
3. #growth
4. #productivity
```

This reveals what's **really** on your mind, not just what you did.

## Cost Tracking Philosophy

### Why Track Costs?

Azure OpenAI charges per token. Second Brain provides transparency:

**Real-time tracking:**
- Every API call recorded with full metadata
- Costs calculated using current Azure pricing
- Local SQLite database (your data, your machine)

**Analysis capabilities:**
- Daily/weekly trends
- Per-operation breakdowns (prompts, links, tags, reports)
- Monthly projections
- Export to JSON for custom analysis

### Ollama = No Cost Tracking

When `LLM_PROVIDER=ollama`:
- Cost tracking is disabled (local = free!)
- No database writes for costs
- All other features work identically
- Privacy benefit: no usage metrics stored

## Technical Philosophy

### Type Safety Over Tests

Python 3.13+ with comprehensive type hints:
```python
def extract_entities(entry: DiaryEntry, llm_client: LLMClient) -> dict[str, list[str]]:
```

**Benefits:**
- Catch errors at development time
- IDE autocomplete and validation
- Self-documenting function signatures
- Refactoring confidence

### Dataclasses for Structure

Use dataclasses, not dicts:
```python
@dataclass
class SemanticLink:
    target_date: str
    confidence: Literal["high", "medium", "low"]
    reason: str
    entities: list[str]
```

**Benefits:**
- Type safety on all fields
- Validation at construction
- Better IDE support
- Clear structure in code

### Constants, Not Magic Numbers

All configuration in `brain_core/constants.py`:
```python
SEMANTIC_TEMPERATURE = 0.7
MAX_SEMANTIC_LINKS = 3
TAG_TEMPERATURE = 0.5
MAX_TOPIC_TAGS = 15
```

**Never hardcode values.** Import constants where needed.

### Single Responsibility Modules

Clear separation:
- `llm_analysis.py` - Atomic LLM operations (stateless)
- `report_generator.py` - Orchestration (stateful)
- `entry_manager.py` - File I/O only (no LLM calls)
- `plan_commands.py` - CLI interface for planning
- `diary_commands.py` - CLI interface for reflection

### Timing Metrics on All LLM Calls

Every LLM operation logs:
```python
start_time = time.time()
# ... LLM call ...
elapsed = time.time() - start_time
logger.info(f"Generated {count} tags in {elapsed:.2f}s")
```

**Purpose:** Understand performance, optimize token usage, debug issues.

## Future Considerations

### What This Could Become

Potential enhancements that align with philosophy:
- 📊 Obsidian plugin for inline prompts
- 🔍 Semantic search across all entries
- 📈 Mood tracking visualization
- 🎯 Goal progress extraction from reflections
- 🧠 Spaced repetition prompts (ask about old entries)

### What This Won't Become

Features that violate core principles:
- ❌ Social/sharing features (private by design)
- ❌ Mobile app (Obsidian mobile works great)
- ❌ Web interface (CLI/local only)
- ❌ Cloud sync service (bring your own)
- ❌ All-in-one productivity suite (stay focused)

---

*The best journaling system is one you actually use. Second Brain removes friction while preserving the human element of reflection.*
