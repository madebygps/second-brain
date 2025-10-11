"""LLM-powered analysis for semantic backlinks and tags."""
from typing import List, Tuple
from .entry_manager import DiaryEntry
from .ollama_client import OllamaClient


def generate_semantic_backlinks(
    target_entry: DiaryEntry,
    candidate_entries: List[DiaryEntry],
    ollama_client: OllamaClient,
    max_links: int = 5
) -> List[str]:
    """Use LLM to find semantically related entries."""
    if not candidate_entries:
        return []

    # Build context with candidates
    candidate_context = []
    for entry in candidate_entries[:20]:  # Limit to 20 most recent to avoid token limits
        if entry.date == target_entry.date:
            continue
        preview = entry.brain_dump[:200] if len(entry.brain_dump) > 200 else entry.brain_dump
        if preview:
            candidate_context.append(f"[[{entry.date.isoformat()}]]: {preview}")

    if not candidate_context:
        return []

    candidates_text = "\n\n".join(candidate_context)
    target_preview = target_entry.brain_dump[:500] if len(target_entry.brain_dump) > 500 else target_entry.brain_dump

    system_prompt = f"""You are analyzing diary entries to find semantic connections. Given a target entry and a list of candidate entries, identify which candidates are most related to the target.

Consider:
- Thematic connections (similar topics, emotions, situations)
- Cause and effect relationships
- Follow-ups or continuations of ideas
- Related people, places, or events

Return ONLY the dates of related entries (up to {max_links}), one per line, in the format YYYY-MM-DD.
If no entries are related, return an empty response.
Do not include explanations or additional text."""

    user_prompt = f"""Target entry [[{target_entry.date.isoformat()}]]:
{target_preview}

---

Candidate entries:
{candidates_text}

---

Which candidate entries are semantically related to the target? Return only the dates (YYYY-MM-DD), one per line, up to {max_links} entries."""

    try:
        response = ollama_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,  # Lower temperature for more focused results
            max_tokens=200
        )

        # Parse dates from response
        dates = []
        for line in response.split("\n"):
            line = line.strip()
            # Match YYYY-MM-DD format
            if len(line) == 10 and line[4] == '-' and line[7] == '-':
                try:
                    # Validate it's a real date
                    parts = line.split('-')
                    if len(parts) == 3 and all(p.isdigit() for p in parts):
                        dates.append(line)
                except:
                    continue

        return dates[:max_links]

    except Exception as e:
        print(f"Warning: LLM backlink generation failed: {e}")
        return []


def generate_semantic_tags(
    entries: List[DiaryEntry],
    ollama_client: OllamaClient,
    max_tags: int = 5
) -> List[str]:
    """Use LLM to generate semantic topic tags."""
    if not entries:
        return []

    # Build context from entries
    context_parts = []
    for entry in entries[:5]:  # Use up to 5 entries for context
        preview = entry.brain_dump[:200] if len(entry.brain_dump) > 200 else entry.brain_dump
        if preview:
            context_parts.append(preview)

    if not context_parts:
        return []

    context = "\n\n".join(context_parts)

    system_prompt = f"""You are analyzing diary entries to extract deep thematic tags. Generate {max_tags} tags that capture the underlying themes, emotions, and psychological patterns - not just surface-level topics.

Good tags identify:
- Emotional states and patterns (e.g., #overwhelm, #fulfillment, #frustration)
- Personal struggles or growth areas (e.g., #boundaries, #patience, #balance)
- Recurring life themes (e.g., #identity, #purpose, #relationships)
- Internal conflicts or tensions (e.g., #perfectionism, #control)

Avoid:
- Generic activity words (e.g., #work, #meeting)
- Obvious nouns from the text (e.g., #python, #book)
- Surface-level descriptions (e.g., #busy, #progress)

Tags should be:
- Thematic and emotionally meaningful
- 3-15 characters, lowercase
- Single words or hyphenated phrases
- No emojis

Return ONLY the tags, one per line, with a # prefix (e.g., #fulfillment, #self-doubt, #growth).
Do not include explanations or additional text."""

    user_prompt = f"""Analyze these diary entries and identify the deep themes, emotional patterns, and underlying concerns:

{context}

---

What are the {max_tags} most meaningful thematic tags that capture the emotional and psychological essence of these entries?
Return only the tags (one per line, with # prefix), focusing on themes over topics."""

    try:
        response = ollama_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.5,
            max_tokens=100
        )

        # Parse tags from response
        tags = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                tag = line[1:].strip().lower()
                # Validate tag length
                if 3 <= len(tag) <= 15 and tag:
                    tags.append(tag)
            elif line and not line.startswith("#") and len(line) <= 15:
                # Handle cases where LLM forgets the # prefix
                tag = line.strip().lower()
                if 3 <= len(tag) <= 15:
                    tags.append(tag)

        return tags[:max_tags]

    except Exception as e:
        print(f"Warning: LLM tag generation failed: {e}")
        return []
