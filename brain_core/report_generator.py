"""Generate formatted analysis reports from diary entries."""
from typing import List, Dict
import re
import logging
import time
from .entry_manager import DiaryEntry
from .llm_client import LLMClient
from .llm_analysis import generate_semantic_backlinks, _truncate_text
from .constants import (
    DEFAULT_THEMES_COUNT,
    MEMORY_TRACE_TOP_THEMES,
    TOP_CONNECTED_ENTRIES,
    MAX_SEMANTIC_LINKS,
    SEMANTIC_TEMPERATURE,
    SEMANTIC_MAX_TOKENS,
    ENTRY_PREVIEW_LENGTH
)

logger = logging.getLogger(__name__)


def _extract_report_themes(entries: List[DiaryEntry], llm_client: LLMClient, top_n: int = DEFAULT_THEMES_COUNT) -> List[str]:
    """Extract meaningful themes using LLM analysis for report generation.
    
    Private helper function for create_memory_trace_report().
    
    Args:
        entries: List of diary entries to analyze
        llm_client: LLM client for semantic analysis
        top_n: Number of themes to extract
        
    Returns:
        List of theme names (strings) identified by the LLM
    """
    if not entries:
        return []
    
    # Take a sample of entries (limit for token efficiency)
    sample_entries = entries[:20] if len(entries) > 20 else entries
    
    # Build context with entry previews
    entry_previews = []
    for entry in sample_entries:
        preview = _truncate_text(entry.brain_dump, ENTRY_PREVIEW_LENGTH)
        entry_previews.append(f"[{entry.date.isoformat()}]: {preview}")
    
    combined_text = "\n\n".join(entry_previews)
    
    system_prompt = f"""Analyze these diary entries and identify the {top_n} most significant recurring themes or topics.

Focus on:
- Main activities and projects
- Recurring concerns or interests  
- Emotional patterns
- Life areas (work, relationships, health, learning, hobbies)
- Specific subjects or goals being worked on

Return ONLY the theme names as a simple list, one per line. Be specific and meaningful.
Do not include numbers, bullets, or explanations - just the theme names.

Entries:
{combined_text}"""
    
    try:
        start_time = time.time()
        response = llm_client.generate_sync(
            prompt=system_prompt,
            system="",  # No separate system prompt needed
            temperature=SEMANTIC_TEMPERATURE,
            max_tokens=SEMANTIC_MAX_TOKENS
        )
        elapsed = time.time() - start_time
        
        # Parse response - extract clean theme names
        themes = []
        for line in response.strip().split('\n'):
            # Clean up the line
            theme = line.strip()
            # Remove common prefixes like "1.", "-", "*", etc.
            theme = re.sub(r'^[\d\-\*\.\)\]]+\s*', '', theme)
            theme = theme.strip()
            
            if theme and len(theme) > 2:
                themes.append(theme)
                if len(themes) >= top_n:
                    break
        
        logger.debug(f"Extracted {len(themes)} themes in {elapsed:.2f}s from {len(entries)} entries")
        return themes if themes else ["No clear themes identified"]
        
    except RuntimeError as e:
        logger.warning(f"LLM theme extraction failed for {len(entries)} entries - {e}")
        return ["Error extracting themes"]
    except Exception as e:
        logger.error(f"Unexpected error in theme extraction - {e}")
        return ["Error extracting themes"]


def create_memory_trace_report(entries: List[DiaryEntry], llm_client: LLMClient) -> str:
    """Create a memory trace analysis report for a period of entries.
    
    Args:
        entries: List of diary entries to analyze
        llm_client: LLM client for semantic analysis and theme extraction
    
    Returns:
        Formatted markdown report with themes and connected entries
    """
    if not entries:
        return "No entries found for analysis."

    # Sort entries by date
    sorted_entries = sorted(entries, key=lambda e: e.date)

    # Build report header
    lines = [
        "# Memory Trace Analysis",
        "",
        f"**Period:** {sorted_entries[0].date.isoformat()} to {sorted_entries[-1].date.isoformat()}",
        f"**Entries:** {len(sorted_entries)}",
        "",
        "## Recurring Themes",
        ""
    ]

    # Extract themes using LLM
    themes = _extract_report_themes(sorted_entries, llm_client, top_n=MEMORY_TRACE_TOP_THEMES)
    for i, theme in enumerate(themes[:DEFAULT_THEMES_COUNT], 1):
        lines.append(f"{i}. **{theme}**")

    # Find highly connected entries (most related to others)
    lines.append("")
    lines.append("## Most Connected Entries")
    lines.append("")

    entry_connections: Dict[str, int] = {}
    
    # Use LLM semantic analysis for similarity detection
    for entry in sorted_entries:
        # Get other entries as candidates
        candidates = [e for e in sorted_entries if e.date != entry.date]
        if candidates:
            # Returns List[SemanticLink] with metadata
            semantic_links = generate_semantic_backlinks(
                entry,
                candidates,
                llm_client,
                max_links=MAX_SEMANTIC_LINKS
            )
            if semantic_links:
                entry_connections[entry.date.isoformat()] = len(semantic_links)

    # Sort by number of connections
    top_connected = sorted(entry_connections.items(), key=lambda x: x[1], reverse=True)[:TOP_CONNECTED_ENTRIES]

    for date_str, num_connections in top_connected:
        lines.append(f"- [[{date_str}]] ({num_connections} related entries)")

    return "\n".join(lines)
