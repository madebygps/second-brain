# Planning Guide

Complete guide to the `brain plan` commands for morning task planning.

## Overview

The planning system extracts actionable tasks from your reflections and manages daily todos. Tasks are stored separately from your diary in `PLANNER_PATH`.

**Key Features:**
- LLM extracts actionable items from yesterday's diary
- Automatically carries forward unchecked todos
- Backlinks to source entries
- Simple, distraction-free format

## Commands

```bash
brain plan create today       # Create today's plan
brain plan create tomorrow    # Create tomorrow's plan
```

## Entry Format

**Filename:** `YYYY-MM-DD-plan.md` (e.g., `2025-10-15-plan.md`)
**Location:** `PLANNER_PATH` (separate from diary)

### Structure

```markdown
## Action Items
- [ ] Task extracted from yesterday's diary (from [[2025-10-14]])
- [ ] Uncompleted task from yesterday's plan (from [[2025-10-14-plan]])
- [ ] Another actionable item (from [[2025-10-14]])
```

### Features

**Intelligent Task Extraction:**
- Analyzes yesterday's diary entry with LLM (temperature=0.4)
- Extracts only actionable tasks
- Filters out completed activities and vague intentions
- Includes backlinks to source entries

**Automatic Carryforward:**
- Finds unchecked todos from yesterday's plan
- Preserves original backlinks
- Deduplicates similar tasks

**Simple Format:**
- Action Items section only (no prompts)
- Standard markdown checkboxes `- [ ]`
- Obsidian-compatible wiki links `[[YYYY-MM-DD]]`

### Example

```markdown
## Action Items
- [ ] Follow up with Sarah about Q4 planning (from [[2025-10-14]])
- [ ] Review pull requests for API refactor (from [[2025-10-14]])
- [ ] Schedule dentist appointment (from [[2025-10-13-plan]])
- [ ] Research deployment options (from [[2025-10-14]])
```

## What Gets Extracted

The LLM analyzes yesterday's diary and intelligently identifies actionable tasks:

### ✅ Included

**Incomplete tasks:**
- "Still need to review the PR"
- "Haven't finished the report yet"

**Future intentions with specifics:**
- "Will reach out to Sarah tomorrow"
- "Want to research deployment options"
- "Need to schedule that appointment"

**Follow-ups from meetings:**
- "Should follow up with the team about..."
- "Going to send that email to..."

**Blockers requiring action:**
- "Waiting for response from client about X"
- "Blocked on getting access to Y"

### ❌ Excluded

**Completed activities:**
- "Finished the report"
- "Sent the email"
- "Completed the review"

**Social activities without clear next steps:**
- "Had coffee with Alex"
- "Caught up with the team"

**Emotional reflections:**
- "Feeling overwhelmed"
- "Anxious about the deadline"

**Vague intentions:**
- "Should be more productive"
- "Need to focus more"
- "Want to do better"

**Past activities:**
- "Went to the gym"
- "Had dinner with friends"
- "Watched a movie"

## Daily Workflow

### Morning Routine (5 minutes)

```bash
# 1. Create today's plan
brain plan create today

# 2. Review the generated tasks
# - Open PLANNER_PATH/YYYY-MM-DD-plan.md
# - Add/remove/edit tasks as needed
# - Manually add any tasks not extracted

# 3. Start your day!
```

**Tips:**
- Review tasks but don't over-optimize
- Add context to unclear tasks
- Manually add recurring tasks (gym, meditation, etc.)
- It's okay to skip days - the system adapts

### During the Day

- Check off tasks as you complete them: `- [x]`
- Add new tasks that come up
- Don't stress about perfect tracking

### Evening

The plan stays as-is. Your evening reflection (diary) is separate.

## Customization

### Manual Editing

Plans are plain markdown - edit freely:

```markdown
## Action Items
- [ ] LLM-extracted task (from [[2025-10-14]])
- [ ] Manually added task
- [ ] Another manual task with context: needs to happen before 2pm
```

**The system won't overwrite your changes.** Next day's plan will:
- Carry forward unchecked LLM-extracted tasks
- Carry forward unchecked manual tasks
- Add new LLM-extracted tasks from yesterday's diary

### Custom Sections

Add your own structure:

```markdown
## Action Items
- [ ] Task 1 (from [[2025-10-14]])
- [ ] Task 2 (from [[2025-10-14]])

## Priorities
1. Most important task
2. Second priority

## Notes
- Meeting at 2pm
- Remember to call back about X
```

The system only looks for `- [ ]` todos in the file, regardless of section.

## How Task Extraction Works

### LLM Configuration

- **Model:** Your configured provider (Azure OpenAI or Ollama)
- **Temperature:** 0.4 (balanced creativity and consistency)
- **Max Tokens:** Configurable via `TASK_EXTRACTION_MAX_TOKENS`

### Analysis Process

1. **Read yesterday's diary:** Loads the Brain Dump section
2. **Identify actionable items:** LLM analyzes for tasks with specific criteria
3. **Add backlinks:** Each task includes `(from [[YYYY-MM-DD]])`
4. **Load yesterday's plan:** Finds unchecked todos
5. **Deduplicate:** Removes similar tasks between diary and plan
6. **Generate file:** Creates today's plan with combined tasks

### Example Transformation

**Yesterday's diary (2025-10-14.md):**
```markdown
## Brain Dump
Today was productive. Finished the API documentation and sent it to
the team. Still need to review Sarah's PR before the meeting tomorrow.

Had a good conversation with Alex about the database migration - we
decided to go with approach B. I should research the performance
implications before we commit.

Went to the gym in the evening. Feeling good about consistent exercise.
```

**Yesterday's plan (2025-10-14-plan.md):**
```markdown
## Action Items
- [x] Finish API documentation
- [ ] Schedule dentist appointment
- [x] Review database options
```

**Today's generated plan (2025-10-15-plan.md):**
```markdown
## Action Items
- [ ] Review Sarah's PR (from [[2025-10-14]])
- [ ] Research database performance implications for approach B (from [[2025-10-14]])
- [ ] Schedule dentist appointment (from [[2025-10-14-plan]])
```

Notice how it:
- ✅ Extracted "still need to review Sarah's PR"
- ✅ Extracted "should research the performance implications"
- ✅ Carried forward unchecked dentist appointment
- ❌ Ignored "Finished the API documentation" (completed)
- ❌ Ignored "Had a good conversation" (past activity)
- ❌ Ignored "Went to the gym" (past activity)

## Obsidian Integration

### Graph View

Plan backlinks create connections in Obsidian's graph view:
- See which diary entries generated which tasks
- Trace task origins over time
- Understand task patterns

### Daily Notes vs. Plans

**Keep them separate:**

- **Second Brain Plans** (`PLANNER_PATH`): Generated todos from reflections
- **Obsidian Daily Notes**: Meeting notes, logs, quick captures

Both can coexist in the same vault if desired, just use different directories.

### Mobile Access

Use Obsidian mobile to:
- Check off tasks during the day
- Add new tasks on the go
- Plans sync like any markdown file

## Tips & Best Practices

### Start Simple

Don't try to extract every possible task:
- Focus on actual next actions
- Skip recurring habits (those are automatic)
- Ignore "should" statements that aren't real intentions

### Trust the System

The LLM isn't perfect, but it's consistent:
- Review and adjust generated tasks
- Add what it missed
- Remove what doesn't make sense
- It learns your patterns over time (via your editing)

### Separate Planning from Reflection

**Morning (plan):** What needs to happen?
**Evening (diary):** What actually happened and how did it feel?

Don't mix them. The separation is intentional and valuable.

### Don't Overthink It

Plans are meant to be:
- ⏱️ Quick (5 minutes max)
- 📝 Simple (checkboxes and text)
- 🔄 Flexible (edit throughout the day)

If you're spending 30 minutes planning, you're overthinking it.

### When to Skip

It's okay to skip planning:
- Weekends (if that fits your rhythm)
- Vacation days
- Days with no real tasks

The system doesn't punish gaps. Plans are a tool, not a requirement.

## LLM Provider Notes

### With Ollama (Local)

- Task extraction happens on your machine
- Slightly slower than Azure (3-5 seconds)
- Completely private - diary content never leaves your computer
- No cost tracking

### With Azure OpenAI

- Task extraction uses cloud API
- Faster (1-2 seconds)
- Costs ~$0.001-0.005 per plan generation
- Usage tracked in cost database

Both providers produce identical functionality.

## Troubleshooting

### No tasks extracted

**Possible reasons:**
- Yesterday's diary was mostly reflection, not action-oriented
- Tasks were described vaguely ("should do better")
- Everything was completed ("finished X, Y, Z")

**Solution:** Manually add tasks if needed. The LLM extracts what it can.

### Too many tasks extracted

**Possible reasons:**
- Yesterday's diary was very task-heavy
- LLM interpreted reflections as intentions

**Solution:** Delete irrelevant tasks. The system learns from what you keep.

### Duplicate tasks

**Should be rare** (deduplication is built-in), but if it happens:
- Delete duplicates manually
- Report as a bug if systematic

### Tasks from wrong day

**Check:**
- Are you running `brain plan create today`?
- Is your system date correct?
- Are diary files named correctly (YYYY-MM-DD.md)?

---

*Planning should feel like a helpful assistant, not a chore. Adjust the system to fit your needs.*
