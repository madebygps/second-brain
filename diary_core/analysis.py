"""Extract themes and find related entries using Jaccard similarity."""
from typing import List, Dict, Tuple, Set
from collections import Counter
import re
from .entry_manager import DiaryEntry


def extract_words(text: str) -> Set[str]:
    """Extract meaningful words from text (lowercase, no stopwords)."""
    # Common stopwords to ignore
    stopwords = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
        "been", "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "can", "i", "you",
        "he", "she", "it", "we", "they", "my", "your", "his", "her", "its",
        "our", "their", "this", "that", "these", "those", "am", "what", "when",
        "where", "why", "how", "all", "each", "every", "both", "few", "more",
        "most", "other", "some", "such", "no", "not", "only", "own", "same",
        "so", "than", "too", "very", "just", "now", "then", "there", "here"
    }

    # Extract words (alphanumeric only, lowercase)
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())

    # Filter out stopwords
    return {w for w in words if w not in stopwords}


def jaccard_similarity(set1: Set[str], set2: Set[str]) -> float:
    """Calculate Jaccard similarity between two sets."""
    if not set1 or not set2:
        return 0.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)

    return intersection / union if union > 0 else 0.0


def find_related_entries(
    target_entry: DiaryEntry,
    candidate_entries: List[DiaryEntry],
    threshold: float = 0.08  # 8% Jaccard similarity
) -> List[Tuple[DiaryEntry, float]]:
    """Find entries related to target entry based on Jaccard similarity."""
    target_words = extract_words(target_entry.brain_dump)

    if not target_words:
        return []

    related = []
    for candidate in candidate_entries:
        # Don't compare entry with itself
        if candidate.date == target_entry.date:
            continue

        candidate_words = extract_words(candidate.brain_dump)
        similarity = jaccard_similarity(target_words, candidate_words)

        if similarity >= threshold:
            related.append((candidate, similarity))

    # Sort by similarity (highest first)
    related.sort(key=lambda x: x[1], reverse=True)

    return related


def extract_themes(entries: List[DiaryEntry], top_n: int = 10) -> List[Tuple[str, int]]:
    """Extract most common themes (words) from entries."""
    all_words: List[str] = []

    for entry in entries:
        words = extract_words(entry.brain_dump)
        all_words.extend(words)

    # Count word frequencies
    word_counts = Counter(all_words)

    # Return top N most common
    return word_counts.most_common(top_n)


def extract_todos(entry: DiaryEntry) -> List[str]:
    """Extract action items/todos from entry content."""
    todos = []

    # Look for common todo patterns
    patterns = [
        r'(?:^|\n)[-*•]\s*(?:TODO|To do|Action):\s*(.+?)(?:\n|$)',  # - TODO: item
        r'(?:^|\n)[-*•]\s*\[ \]\s*(.+?)(?:\n|$)',  # - [ ] item (checkbox)
        r'(?:^|\n)(?:TODO|To do|Action):\s*(.+?)(?:\n|$)',  # TODO: item
        r'(?:^|\n)(?:I need to|I should|I must|I will)\s+(.+?)(?:\.|$)',  # Natural language
    ]

    content = entry.content

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            todo = match.group(1).strip()
            if todo and len(todo) > 3:  # Filter out very short matches
                todos.append(todo)

    return todos


def generate_topic_tags(entries: List[DiaryEntry], max_tags: int = 5) -> List[str]:
    """Generate topic tags based on recurring themes."""
    themes = extract_themes(entries, top_n=max_tags * 2)

    # Filter themes to good tag candidates (3-15 chars, common enough)
    tags = []
    for theme, count in themes:
        if 3 <= len(theme) <= 15 and count >= 2:
            tags.append(theme)
            if len(tags) >= max_tags:
                break

    return tags


def create_memory_trace_report(entries: List[DiaryEntry]) -> str:
    """Create a memory trace analysis report for a period of entries."""
    if not entries:
        return "No entries found for analysis."

    # Sort entries by date
    sorted_entries = sorted(entries, key=lambda e: e.date)

    # Extract themes
    themes = extract_themes(sorted_entries, top_n=15)

    # Build report
    lines = [
        f"# Memory Trace Analysis",
        f"",
        f"**Period:** {sorted_entries[0].date.isoformat()} to {sorted_entries[-1].date.isoformat()}",
        f"**Entries:** {len(sorted_entries)}",
        f"",
        f"## Recurring Themes",
        f""
    ]

    for i, (theme, count) in enumerate(themes[:10], 1):
        lines.append(f"{i}. **{theme}** ({count} occurrences)")

    # Find highly connected entries (most related to others)
    lines.append("")
    lines.append("## Most Connected Entries")
    lines.append("")

    entry_connections: Dict[str, int] = {}
    for entry in sorted_entries:
        related = find_related_entries(entry, sorted_entries, threshold=0.08)
        if related:
            entry_connections[entry.date.isoformat()] = len(related)

    # Sort by number of connections
    top_connected = sorted(entry_connections.items(), key=lambda x: x[1], reverse=True)[:5]

    for date_str, num_connections in top_connected:
        lines.append(f"- [[{date_str}]] ({num_connections} related entries)")

    return "\n".join(lines)
