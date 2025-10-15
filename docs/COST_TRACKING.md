# Cost Tracking Guide

Complete guide to the `brain cost` commands for Azure OpenAI usage tracking.

## Overview

When using Azure OpenAI as your LLM provider, every API call is tracked in a local SQLite database. This gives you complete visibility into costs, usage patterns, and optimization opportunities.

**Key Features:**
- Real-time cost calculation
- Per-operation breakdowns
- Daily/weekly/monthly trends
- Cost projections
- Export to JSON
- Local storage (your data stays private)

**Note:** Cost tracking is disabled when using Ollama (local LLM = free!).

## Commands

```bash
brain cost summary           # Usage summary for last 30 days
brain cost trends <days>     # Daily cost trends (default: 30)
brain cost breakdown         # Per-operation cost breakdown
brain cost estimate          # Monthly cost projection
brain cost export <file>     # Export to JSON
brain cost pricing           # Show current pricing
```

## What Gets Tracked

### Every LLM Call Records

- **Timestamp:** When the call was made
- **Operation:** What triggered it (prompts, backlinks, tags, report, etc.)
- **Model:** Azure deployment name (e.g., gpt-4o)
- **Tokens:** Input, output, and total token counts
- **Cost:** Calculated based on Azure pricing
- **Duration:** How long the call took (seconds)
- **Entry Date:** Which diary entry was being processed (if applicable)

### Metadata Captured

For optimization and debugging:
- Temperature setting
- Max tokens limit
- Prompt length (characters)
- Response length (characters)
- System prompt length (characters)

### Database Location

Default: `~/.brain/costs.db`
Configurable via: `BRAIN_COST_DB_PATH` in `.env`

**Database size:** Grows ~10-50 MB per year of typical usage.

## Command Details

### Summary

```bash
brain cost summary
```

**Shows:**
- Total cost for last 30 days
- Total API calls made
- Average cost per call
- Total tokens used (input/output)
- Most expensive operations

**Example output:**
```
Cost Summary (Last 30 Days)

Total Cost: $2.34
Total Calls: 156
Avg Cost/Call: $0.015
Total Tokens: 78,450 (52,300 input, 26,150 output)

Top Operations:
1. backlinks: $0.89 (38%)
2. prompts: $0.67 (29%)
3. tags: $0.45 (19%)
4. report: $0.33 (14%)
```

### Trends

```bash
brain cost trends 30    # Last 30 days
brain cost trends 7     # Last week
```

**Shows:**
- Daily cost breakdown
- Visual ASCII graph
- Total for period

**Example output:**
```
Daily Cost Trends (Last 7 Days)

Oct 09: $0.12 ████████████
Oct 10: $0.08 ████████
Oct 11: $0.15 ███████████████
Oct 12: $0.05 █████
Oct 13: $0.00 (no activity)
Oct 14: $0.18 ██████████████████
Oct 15: $0.11 ███████████

Total: $0.69
```

### Breakdown

```bash
brain cost breakdown
```

**Shows:**
- Cost by operation type
- Percentage of total
- Average cost per operation
- Call count

**Example output:**
```
Cost Breakdown by Operation (Last 30 Days)

Operation      Cost      Calls   Avg Cost   Percentage
─────────────────────────────────────────────────────
backlinks      $0.89     45      $0.020     38%
prompts        $0.67     30      $0.022     29%
tags           $0.45     45      $0.010     19%
report         $0.33     6       $0.055     14%

Total          $2.34     126     $0.019     100%
```

**Operations explained:**
- `prompts` - Generating reflection prompts
- `backlinks` - Finding semantic connections
- `tags` - Extracting psychological themes
- `report` - Memory trace analysis
- `patterns` - Pattern identification
- `entities` - Extracting people/places/projects
- `task_extraction` - Extracting tasks from diary

### Estimate

```bash
brain cost estimate
```

**Shows:**
- Projected monthly cost based on recent usage
- Daily average
- Confidence in projection

**Example output:**
```
Monthly Cost Estimate

Based on last 30 days:
Daily Average: $0.08
Monthly Projection: $2.40

Note: Projection assumes consistent usage patterns.
Actual costs may vary based on entry length and frequency.
```

### Export

```bash
brain cost export costs.json
```

**Exports all cost data to JSON** for custom analysis:

```json
[
  {
    "timestamp": "2025-10-15T23:30:15",
    "operation": "backlinks",
    "model": "gpt-4o",
    "prompt_tokens": 1200,
    "completion_tokens": 450,
    "total_tokens": 1650,
    "cost": 0.063,
    "elapsed_seconds": 1.23,
    "entry_date": "2025-10-15",
    "metadata": {
      "temperature": 0.7,
      "max_tokens": 2000,
      "prompt_length": 4850,
      "response_length": 892
    }
  }
]
```

Use for:
- Custom visualizations
- Expense reports
- Usage analysis
- Optimization research

### Pricing

```bash
brain cost pricing
```

**Shows current pricing configuration:**

```
Azure OpenAI Pricing

gpt-4o:
  Input:  $0.030 per 1K tokens
  Output: $0.060 per 1K tokens

gpt-4o-mini:
  Input:  $0.0015 per 1K tokens
  Output: $0.006 per 1K tokens

gpt-4:
  Input:  $0.030 per 1K tokens
  Output: $0.060 per 1K tokens

gpt-35-turbo:
  Input:  $0.0015 per 1K tokens
  Output: $0.002 per 1K tokens

Note: Prices are configurable via environment variables.
See SETUP_CHECKLIST.md for custom pricing configuration.
```

## Cost Optimization

### Understand Your Usage

Run `brain cost breakdown` monthly to see:
- Which operations cost the most
- Whether you're using features you don't need
- Opportunities to optimize

### Choose Operations Wisely

**Most expensive** (detailed analysis):
- `brain diary report 30` - Analyzes 30 entries deeply
- `brain diary refresh 30` - Regenerates links for 30 entries

**Moderately expensive** (per entry):
- `brain diary link today` - Semantic analysis of one entry
- `brain plan create today` - Task extraction from one entry

**Least expensive** (quick operations):
- `brain diary create today` - Just prompts, no analysis
- `brain diary list` - No LLM calls

### Optimize Frequency

**Daily (low cost):**
- ✅ `brain diary create today`
- ✅ `brain diary link today`
- ✅ `brain plan create today`

**Weekly (moderate cost):**
- ✅ `brain diary report 7`
- ✅ `brain diary patterns 7`

**Monthly (higher cost):**
- ⚠️ `brain diary report 30`
- ⚠️ `brain diary refresh 30`

### Consider Ollama

If costs are a concern:
1. Install Ollama (free, local)
2. Set `LLM_PROVIDER=ollama` in `.env`
3. Pull a model: `ollama pull llama3.1`
4. Zero ongoing costs!

**Tradeoffs:**
- Slightly slower (3-5s vs 1-2s)
- Runs on your hardware (uses CPU/GPU)
- 100% private (no cloud calls)
- Identical functionality

## Typical Cost Examples

Based on actual usage patterns:

### Light User (2-3 entries/week)

**Monthly activities:**
- 10 diary entries with linking
- 10 plan creations
- 1-2 weekly reports

**Estimated cost:** $0.50 - $1.50/month

### Regular User (5-7 entries/week)

**Monthly activities:**
- 25 diary entries with linking
- 25 plan creations
- 4 weekly reports
- 1 monthly report

**Estimated cost:** $2.00 - $4.00/month

### Heavy User (daily + analysis)

**Monthly activities:**
- 30 diary entries with linking
- 30 plan creations
- 4 weekly reports
- 2 monthly reports
- Occasional refresh operations

**Estimated cost:** $4.00 - $8.00/month

### Cost Comparison

For context:
- Netflix subscription: ~$15/month
- Spotify: ~$10/month
- Coffee habit: $5/day = $150/month
- Second Brain: $2-8/month

## Custom Pricing Configuration

Azure pricing varies by region and agreement. Override defaults in `.env`:

```bash
# Custom pricing (price per 1K tokens)
AZURE_GPT4O_INPUT_PRICE=0.025      # Instead of default 0.03
AZURE_GPT4O_OUTPUT_PRICE=0.055     # Instead of default 0.06
```

Available variables:
- `AZURE_GPT4O_INPUT_PRICE`
- `AZURE_GPT4O_OUTPUT_PRICE`
- `AZURE_GPT4O_MINI_INPUT_PRICE`
- `AZURE_GPT4O_MINI_OUTPUT_PRICE`
- `AZURE_GPT4_INPUT_PRICE`
- `AZURE_GPT4_OUTPUT_PRICE`
- `AZURE_GPT35_TURBO_INPUT_PRICE`
- `AZURE_GPT35_TURBO_OUTPUT_PRICE`

Check your Azure portal for exact pricing in your region.

## Privacy & Data

### What's Stored Locally

Your SQLite database (`~/.brain/costs.db`) contains:
- ✅ Token counts and costs
- ✅ Operation types and timestamps
- ✅ Model names and entry dates
- ✅ Performance metrics
- ❌ **No actual diary content**
- ❌ **No prompts or responses**

### Sharing Cost Data

Safe to share `brain cost export` output:
- No personal information
- No diary content
- Just usage metrics

Use for:
- Expense reports
- Team comparisons
- Optimization discussions

### Database Backup

Consider backing up costs.db:
```bash
cp ~/.brain/costs.db ~/backups/costs-$(date +%Y%m%d).db
```

Especially useful for:
- Tax records (if claiming as business expense)
- Long-term usage analysis
- Preventing data loss

## Troubleshooting

### "Cost tracking disabled (using Ollama)"

This is expected! Ollama is local and free, so there's nothing to track.

### Costs seem high

**Check:**
1. `brain cost breakdown` - Which operations cost most?
2. Are you running `refresh` operations frequently?
3. Are entries very long? (Costs scale with content length)
4. Consider switching to Ollama for zero costs

### Missing cost data

**Possible causes:**
- Database file doesn't exist (creates automatically on first use)
- Permission issues with `~/.brain/` directory
- Using Ollama (intentionally no tracking)

### Export fails

**Check:**
- File path is writable
- Directory exists
- No permission issues

---

*Cost tracking brings transparency to LLM usage. Use it to optimize your workflow and budget.*
