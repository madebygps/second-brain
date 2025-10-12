"""LLM-powered analysis for semantic backlinks and tags."""
from typing import List, Tuple, Dict, Optional
import json
from .entry_manager import DiaryEntry
from .llm_client import LLMClient
from .constants import (
    MAX_SEMANTIC_LINK_CANDIDATES,
    MAX_SEMANTIC_LINKS,
    MAX_TOPIC_TAGS,
    ENTRY_PREVIEW_LENGTH,
    TARGET_PREVIEW_LENGTH,
    SEMANTIC_TEMPERATURE,
    SEMANTIC_MAX_TOKENS,
    TAG_TEMPERATURE,
    TAG_MAX_TOKENS,
    MIN_TAG_LENGTH,
    MAX_TAG_LENGTH
)


class SemanticLink:
    """Represents a semantic link with metadata."""
    def __init__(self, target_date: str, confidence: str, reason: str, entities: List[str]):
        self.target_date = target_date
        self.confidence = confidence  # "high", "medium", "low"
        self.reason = reason
        self.entities = entities  # Related entities/themes


def extract_entities(
    entry: DiaryEntry,
    llm_client: LLMClient
) -> Dict[str, List[str]]:
    """Extract people, places, projects, and themes from an entry."""
    if not entry.brain_dump or len(entry.brain_dump) < 50:
        return {"people": [], "places": [], "projects": [], "themes": []}

    preview = entry.brain_dump[:ENTRY_PREVIEW_LENGTH]

    system_prompt = """You are extracting structured entities from diary entries. Identify:
- People: Names or roles of people mentioned
- Places: Locations, venues, cities
- Projects: Work projects, personal initiatives, ongoing activities
- Themes: Abstract concepts, emotions, or situations (e.g., "career growth", "family tension", "creativity")

Return ONLY a valid JSON object with these four keys, each containing an array of strings.
Keep entries concise (1-3 words each). Return empty arrays if none found.

Example:
{"people": ["Sarah", "manager"], "places": ["office", "coffee shop"], "projects": ["website redesign"], "themes": ["stress", "motivation"]}"""

    user_prompt = f"""Extract entities from this diary entry:

{preview}

Return JSON only (no explanations):"""

    try:
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.2,
            max_tokens=200
        )

        # Try to parse JSON response
        # Remove markdown code blocks if present
        clean_response = response.strip()
        if clean_response.startswith("```"):
            lines = clean_response.split("\n")
            clean_response = "\n".join(lines[1:-1] if len(lines) > 2 else lines)

        entities = json.loads(clean_response)

        # Validate structure
        required_keys = {"people", "places", "projects", "themes"}
        if not all(key in entities for key in required_keys):
            return {"people": [], "places": [], "projects": [], "themes": []}

        return entities

    except (json.JSONDecodeError, RuntimeError) as e:
        print(f"Warning: Entity extraction failed: {e}")
        return {"people": [], "places": [], "projects": [], "themes": []}


def generate_semantic_backlinks_enhanced(
    target_entry: DiaryEntry,
    candidate_entries: List[DiaryEntry],
    llm_client: LLMClient,
    max_links: int = MAX_SEMANTIC_LINKS
) -> List[SemanticLink]:
    """Use LLM to find semantically related entries with confidence scores and bidirectional validation."""
    if not candidate_entries:
        return []

    # Step 1: Extract entities from target entry
    target_entities = extract_entities(target_entry, llm_client)

    # Step 2: Build enriched context with entity information
    candidate_context = []
    candidate_entities_map = {}

    for entry in candidate_entries[:MAX_SEMANTIC_LINK_CANDIDATES]:
        if entry.date == target_entry.date:
            continue

        # Extract entities for each candidate
        entities = extract_entities(entry, llm_client)
        candidate_entities_map[entry.date.isoformat()] = entities

        preview = entry.brain_dump[:ENTRY_PREVIEW_LENGTH] if len(entry.brain_dump) > ENTRY_PREVIEW_LENGTH else entry.brain_dump
        if preview:
            entity_summary = []
            if entities["people"]:
                entity_summary.append(f"People: {', '.join(entities['people'][:3])}")
            if entities["themes"]:
                entity_summary.append(f"Themes: {', '.join(entities['themes'][:3])}")

            entity_str = f" [{'; '.join(entity_summary)}]" if entity_summary else ""
            candidate_context.append(f"[[{entry.date.isoformat()}]]{entity_str}: {preview}")

    if not candidate_context:
        return []

    candidates_text = "\n\n".join(candidate_context)
    target_preview = target_entry.brain_dump[:TARGET_PREVIEW_LENGTH] if len(target_entry.brain_dump) > TARGET_PREVIEW_LENGTH else target_entry.brain_dump

    target_entity_summary = []
    if target_entities["people"]:
        target_entity_summary.append(f"People: {', '.join(target_entities['people'][:3])}")
    if target_entities["themes"]:
        target_entity_summary.append(f"Themes: {', '.join(target_entities['themes'][:3])}")
    target_entity_str = f"\n[{'; '.join(target_entity_summary)}]" if target_entity_summary else ""

    system_prompt = f"""You are analyzing diary entries to find semantic connections with high precision.

Consider:
- Shared people, places, or projects (STRONG indicator)
- Thematic connections and emotional patterns
- Cause and effect relationships
- Follow-ups or continuations of ideas
- Similar situations or contexts

For each related entry, provide:
1. Date (YYYY-MM-DD format)
2. Confidence level: "high" (clear connection), "medium" (probable connection), or "low" (weak connection)
3. Brief reason (5-10 words explaining the connection)
4. Related entities (people/themes that connect them)

Return ONLY valid JSON array format:
[
  {{"date": "YYYY-MM-DD", "confidence": "high", "reason": "both discuss project deadline stress", "entities": ["work project", "stress"]}},
  {{"date": "YYYY-MM-DD", "confidence": "medium", "reason": "similar emotional tone", "entities": ["anxiety"]}}
]

Return up to {max_links} entries. If no strong connections exist, return empty array []."""

    user_prompt = f"""Target entry [[{target_entry.date.isoformat()}]]:{target_entity_str}
{target_preview}

---

Candidate entries:
{candidates_text}

---

Which candidates are semantically related? Return JSON array only (no explanations):"""

    try:
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=SEMANTIC_TEMPERATURE,
            max_tokens=400
        )

        # Parse JSON response
        clean_response = response.strip()
        if clean_response.startswith("```"):
            lines = clean_response.split("\n")
            clean_response = "\n".join(lines[1:-1] if len(lines) > 2 else lines)

        links_data = json.loads(clean_response)

        if not isinstance(links_data, list):
            return []

        # Convert to SemanticLink objects
        semantic_links = []
        for link in links_data[:max_links]:
            if isinstance(link, dict) and "date" in link:
                semantic_links.append(SemanticLink(
                    target_date=link.get("date", ""),
                    confidence=link.get("confidence", "medium"),
                    reason=link.get("reason", ""),
                    entities=link.get("entities", [])
                ))

        # Step 3: Bidirectional validation for high-confidence links
        validated_links = []
        for link in semantic_links:
            if link.confidence == "high":
                # Perform reverse check: would B link back to A?
                is_bidirectional = validate_bidirectional_link(
                    target_entry, link, candidate_entries, llm_client
                )
                if is_bidirectional:
                    validated_links.append(link)
                else:
                    # Downgrade confidence if not bidirectional
                    link.confidence = "medium"
                    validated_links.append(link)
            else:
                # Medium/low confidence links don't require bidirectional check
                validated_links.append(link)

        return validated_links

    except (json.JSONDecodeError, RuntimeError) as e:
        print(f"Warning: Enhanced LLM backlink generation failed: {e}")
        return []


def validate_bidirectional_link(
    source_entry: DiaryEntry,
    link: SemanticLink,
    all_entries: List[DiaryEntry],
    llm_client: LLMClient
) -> bool:
    """Validate that the link makes sense in both directions (A→B and B→A)."""
    # Find the target entry
    target_entry = None
    for entry in all_entries:
        if entry.date.isoformat() == link.target_date:
            target_entry = entry
            break

    if not target_entry:
        return False

    # Quick bidirectional check
    source_preview = source_entry.brain_dump[:300]
    target_preview = target_entry.brain_dump[:300]

    system_prompt = """You are validating a proposed connection between two diary entries.
Given Entry A and Entry B, determine if they are genuinely related bidirectionally.

Answer with ONLY "yes" or "no" (no explanations)."""

    user_prompt = f"""Entry A [[{source_entry.date.isoformat()}]]:
{source_preview}

Entry B [[{target_entry.date.isoformat()}]]:
{target_preview}

Proposed connection: "{link.reason}"
Shared elements: {', '.join(link.entities) if link.entities else 'none'}

Is this a valid bidirectional connection (would both entries reasonably link to each other)? Answer yes or no:"""

    try:
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.1,
            max_tokens=10
        )

        answer = response.strip().lower()
        return "yes" in answer

    except RuntimeError:
        # If validation fails, err on the side of caution
        return True


def generate_semantic_backlinks(
    target_entry: DiaryEntry,
    candidate_entries: List[DiaryEntry],
    llm_client: LLMClient,
    max_links: int = MAX_SEMANTIC_LINKS,
    use_enhanced: bool = True
) -> List[str]:
    """Use LLM to find semantically related entries.

    Args:
        use_enhanced: If True, uses enhanced mode with entity extraction,
                     confidence scores, and bidirectional validation.
                     If False, uses legacy simple mode.
    """
    if use_enhanced:
        # Use enhanced version with metadata
        enhanced_links = generate_semantic_backlinks_enhanced(
            target_entry, candidate_entries, llm_client, max_links
        )
        # Return just the dates for backward compatibility
        return [link.target_date for link in enhanced_links]

    # Legacy simple mode
    if not candidate_entries:
        return []

    # Build context with candidates
    candidate_context = []
    for entry in candidate_entries[:MAX_SEMANTIC_LINK_CANDIDATES]:
        if entry.date == target_entry.date:
            continue
        preview = entry.brain_dump[:ENTRY_PREVIEW_LENGTH] if len(entry.brain_dump) > ENTRY_PREVIEW_LENGTH else entry.brain_dump
        if preview:
            candidate_context.append(f"[[{entry.date.isoformat()}]]: {preview}")

    if not candidate_context:
        return []

    candidates_text = "\n\n".join(candidate_context)
    target_preview = target_entry.brain_dump[:TARGET_PREVIEW_LENGTH] if len(target_entry.brain_dump) > TARGET_PREVIEW_LENGTH else target_entry.brain_dump

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
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=SEMANTIC_TEMPERATURE,
            max_tokens=SEMANTIC_MAX_TOKENS
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

    except RuntimeError as e:
        print(f"Warning: LLM backlink generation failed: {e}")
        return []


def generate_semantic_tags(
    entries: List[DiaryEntry],
    llm_client: LLMClient,
    max_tags: int = MAX_TOPIC_TAGS
) -> List[str]:
    """Use LLM to generate semantic topic tags."""
    if not entries:
        return []

    # Build context from entries
    context_parts = []
    for entry in entries[:MAX_TOPIC_TAGS]:
        preview = entry.brain_dump[:ENTRY_PREVIEW_LENGTH] if len(entry.brain_dump) > ENTRY_PREVIEW_LENGTH else entry.brain_dump
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
- {MIN_TAG_LENGTH}-{MAX_TAG_LENGTH} characters, lowercase
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
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=TAG_TEMPERATURE,
            max_tokens=TAG_MAX_TOKENS
        )

        # Parse tags from response
        tags = []
        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                tag = line[1:].strip().lower()
                # Validate tag length
                if MIN_TAG_LENGTH <= len(tag) <= MAX_TAG_LENGTH and tag:
                    tags.append(tag)
            elif line and not line.startswith("#") and len(line) <= MAX_TAG_LENGTH:
                # Handle cases where LLM forgets the # prefix
                tag = line.strip().lower()
                if MIN_TAG_LENGTH <= len(tag) <= MAX_TAG_LENGTH:
                    tags.append(tag)

        return tags[:max_tags]

    except RuntimeError as e:
        print(f"Warning: LLM tag generation failed: {e}")
        return []
