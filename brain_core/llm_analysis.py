"""LLM-powered analysis for semantic backlinks and tags."""
from typing import List, Dict, Literal, cast
from dataclasses import dataclass
import json
import logging
import time
from .entry_manager import DiaryEntry
from .llm_client import LLMClient
from .logging_config import log_operation_timing
from .constants import (
    MAX_SEMANTIC_LINK_CANDIDATES,
    MAX_SEMANTIC_LINKS,
    MAX_TOPIC_TAGS,
    MAX_ENTRIES_FOR_TAG_CONTEXT,
    ENTRY_PREVIEW_LENGTH,
    TARGET_PREVIEW_LENGTH,
    SEMANTIC_TEMPERATURE,
    TAG_TEMPERATURE,
    TAG_MAX_TOKENS,
    MIN_TAG_LENGTH,
    MAX_TAG_LENGTH,
    MIN_CONTENT_FOR_ENTITY_EXTRACTION,
    ENTITY_EXTRACTION_MAX_TOKENS,
    SEMANTIC_BACKLINKS_MAX_TOKENS
)

logger = logging.getLogger(__name__)

# Type alias for confidence levels
ConfidenceLevel = Literal["high", "medium", "low"]

# Empty entity dict for consistent returns
EMPTY_ENTITIES: Dict[str, List[str]] = {
    "people": [],
    "places": [],
    "projects": [],
    "themes": []
}


@dataclass
class SemanticLink:
    """Represents a semantic link with metadata."""
    target_date: str
    confidence: ConfidenceLevel
    reason: str
    entities: List[str]


def _clean_json_response(response: str) -> str:
    """Remove markdown code blocks from LLM JSON responses.
    
    Args:
        response: Raw LLM response that may contain markdown formatting
        
    Returns:
        Cleaned response string ready for JSON parsing
    """
    clean = response.strip()
    if clean.startswith("```"):
        lines = clean.split("\n")
        clean = "\n".join(lines[1:-1] if len(lines) > 2 else lines)
    return clean


def _truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max_length if needed.
    
    Args:
        text: Text to truncate
        max_length: Maximum length in characters
        
    Returns:
        Original text if shorter than max_length, otherwise truncated text
    """
    return text[:max_length] if len(text) > max_length else text


def _validate_entities(entities: Dict[str, List[str]]) -> Dict[str, List[str]]:
    """Validate and clean entity extraction results.
    
    Args:
        entities: Raw entity dictionary from LLM
        
    Returns:
        Validated entity dictionary with required keys and clean values
    """
    required_keys = {"people", "places", "projects", "themes"}
    validated = {}
    
    for key in required_keys:
        if key not in entities or not isinstance(entities[key], list):
            validated[key] = []
        else:
            # Filter out empty strings and ensure all are strings
            validated[key] = [
                str(item).strip() 
                for item in entities[key] 
                if item and str(item).strip()
            ]
    
    return validated


def _validate_confidence(confidence: str) -> ConfidenceLevel:
    """Validate and normalize confidence level.
    
    Args:
        confidence: Raw confidence string from LLM
        
    Returns:
        Valid confidence level, defaulting to 'medium' if invalid
    """
    normalized = confidence.lower().strip()
    if normalized in {"high", "medium", "low"}:
        return cast(ConfidenceLevel, normalized)
    return "medium"


def extract_entities(
    entry: DiaryEntry,
    llm_client: LLMClient
) -> Dict[str, List[str]]:
    """Extract people, places, projects, and themes from an entry.
    
    Args:
        entry: Diary entry to analyze
        llm_client: LLM client for generation
        
    Returns:
        Dictionary with keys: people, places, projects, themes (all lists of strings)
    """
    if not entry.brain_dump or len(entry.brain_dump) < MIN_CONTENT_FOR_ENTITY_EXTRACTION:
        logger.debug(f"Entry {entry.date}: Insufficient content for entity extraction")
        return EMPTY_ENTITIES.copy()

    preview = _truncate_text(entry.brain_dump, ENTRY_PREVIEW_LENGTH)

    system_prompt = """Extract key entities from diary entries. Identify:
- people: Names or roles (e.g., "Sarah", "manager")
- places: Locations (e.g., "office", "Portland")
- projects: Work/personal initiatives (e.g., "website redesign")
- themes: Emotions/concepts (e.g., "stress", "growth")

Return ONLY valid JSON with these 4 keys as string arrays. Keep entries 1-3 words. Empty arrays if none found.

Example: {"people": ["Sarah"], "places": ["office"], "projects": ["website"], "themes": ["stress"]}"""

    user_prompt = f"""Extract entities from this diary entry:

{preview}

Return JSON only (no explanations):"""

    try:
        start_time = time.time()
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.2,
            max_tokens=ENTITY_EXTRACTION_MAX_TOKENS,
            operation="entity_extraction",
            entry_date=entry.date
        )
        elapsed = time.time() - start_time

        # Clean and parse JSON response
        clean_response = _clean_json_response(response)
        entities = json.loads(clean_response)

        # Validate structure and types
        if not isinstance(entities, dict):
            logger.warning(f"Entry {entry.date}: Invalid entity extraction response type")
            return EMPTY_ENTITIES.copy()
        
        validated_entities = _validate_entities(entities)
        
        logger.debug(
            f"Entry {entry.date}: Extracted entities in {elapsed:.2f}s - "
            f"people: {len(validated_entities['people'])}, "
            f"places: {len(validated_entities['places'])}, "
            f"projects: {len(validated_entities['projects'])}, "
            f"themes: {len(validated_entities['themes'])}"
        )
        
        return validated_entities

    except json.JSONDecodeError as e:
        logger.warning(f"Entry {entry.date}: JSON decode error in entity extraction - {e}")
        return EMPTY_ENTITIES.copy()
    except RuntimeError as e:
        logger.warning(f"Entry {entry.date}: LLM error in entity extraction - {e}")
        return EMPTY_ENTITIES.copy()


def generate_semantic_backlinks(
    target_entry: DiaryEntry,
    candidate_entries: List[DiaryEntry],
    llm_client: LLMClient,
    max_links: int = MAX_SEMANTIC_LINKS
) -> List[SemanticLink]:
    """Use LLM to find semantically related entries with confidence scores and entity extraction.
    
    Args:
        target_entry: The entry to find connections for
        candidate_entries: Potential entries to link to
        llm_client: LLM client for generation
        max_links: Maximum number of links to return (must be positive)
        
    Returns:
        List of SemanticLink objects with metadata
        
    Raises:
        ValueError: If max_links is not positive
    """
    if max_links <= 0:
        raise ValueError(f"max_links must be positive, got {max_links}")
    
    if not candidate_entries:
        logger.debug(f"Entry {target_entry.date}: No candidate entries for backlink generation")
        return []

    # Step 1: Extract entities from target entry
    target_entities = extract_entities(target_entry, llm_client)

    # Step 2: Build context with entity information
    candidate_context = []

    for entry in candidate_entries[:MAX_SEMANTIC_LINK_CANDIDATES]:
        if entry.date == target_entry.date:
            continue

        preview = _truncate_text(entry.brain_dump, ENTRY_PREVIEW_LENGTH)
        if preview:
            candidate_context.append(f"[[{entry.date.isoformat()}]]: {preview}")

    if not candidate_context:
        logger.debug(f"Entry {target_entry.date}: No valid candidate context for backlinks")
        return []

    candidates_text = "\n\n".join(candidate_context)
    target_preview = _truncate_text(target_entry.brain_dump, TARGET_PREVIEW_LENGTH)

    target_entity_summary = []
    if target_entities["people"]:
        people_list = target_entities["people"][:3]
        target_entity_summary.append(f"People: {', '.join(people_list)}")
    if target_entities["themes"]:
        themes_list = target_entities["themes"][:3]
        target_entity_summary.append(f"Themes: {', '.join(themes_list)}")
    target_entity_str = f"\n[{'; '.join(target_entity_summary)}]" if target_entity_summary else ""

    system_prompt = f"""Analyze diary entries to find semantic connections. Consider:
- Shared people, places, or projects
- Thematic/emotional patterns
- Cause-effect relationships
- Continuations of ideas

For each related entry provide:
1. date: YYYY-MM-DD format
2. confidence: "high" (clear), "medium" (probable), "low" (weak)
3. reason: Brief explanation (5-10 words)
4. entities: Connecting elements from target entry's context

Return ONLY valid JSON array (up to {max_links} entries):
[{{"date": "YYYY-MM-DD", "confidence": "high", "reason": "discusses same project deadline", "entities": ["work", "stress"]}}]

Empty array [] if no connections."""

    user_prompt = f"""Target entry [[{target_entry.date.isoformat()}]]:{target_entity_str}
{target_preview}

---

Candidate entries:
{candidates_text}

---

Which candidates are semantically related? Return JSON array only (no explanations):"""

    try:
        start_time = time.time()
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=SEMANTIC_TEMPERATURE,
            max_tokens=SEMANTIC_BACKLINKS_MAX_TOKENS,
            operation="semantic_backlinks",
            entry_date=target_entry.date
        )
        elapsed = time.time() - start_time

        # Parse JSON response
        clean_response = _clean_json_response(response)
        links_data = json.loads(clean_response)

        if not isinstance(links_data, list):
            logger.warning(f"Entry {target_entry.date}: Backlink response not a list")
            return []

        # Convert to SemanticLink objects with validation
        semantic_links = []
        for link in links_data[:max_links]:
            if not isinstance(link, dict) or "date" not in link:
                continue
                
            # Validate and clean entities
            entities = link.get("entities", [])
            if not isinstance(entities, list):
                entities = []
            else:
                entities = [e for e in entities if e]
            
            # Validate confidence level
            confidence = _validate_confidence(link.get("confidence", "medium"))
            
            semantic_links.append(SemanticLink(
                target_date=link.get("date", ""),
                confidence=confidence,
                reason=link.get("reason", ""),
                entities=entities
            ))

        logger.info(
            f"Entry {target_entry.date}: Generated {len(semantic_links)} semantic backlinks "
            f"in {elapsed:.2f}s from {len(candidate_context)} candidates"
        )
        
        return semantic_links

    except json.JSONDecodeError as e:
        logger.warning(f"Entry {target_entry.date}: JSON decode error in backlink generation - {e}")
        return []
    except RuntimeError as e:
        logger.warning(f"Entry {target_entry.date}: LLM error in backlink generation - {e}")
        return []


def generate_semantic_tags(
    entries: List[DiaryEntry],
    llm_client: LLMClient,
    max_tags: int = MAX_TOPIC_TAGS
) -> List[str]:
    """Use LLM to generate semantic topic tags.
    
    Args:
        entries: List of diary entries to analyze
        llm_client: LLM client for generation
        max_tags: Maximum number of tags to return (must be positive)
        
    Returns:
        List of lowercase tag strings (without # prefix)
        
    Raises:
        ValueError: If max_tags is not positive
    """
    if max_tags <= 0:
        raise ValueError(f"max_tags must be positive, got {max_tags}")
    
    if not entries:
        logger.debug("No entries provided for tag generation")
        return []

    # Build context from entries
    context_parts = []
    for entry in entries[:MAX_ENTRIES_FOR_TAG_CONTEXT]:
        preview = _truncate_text(entry.brain_dump, ENTRY_PREVIEW_LENGTH)
        if preview:
            context_parts.append(preview)

    if not context_parts:
        logger.debug("No valid entry content for tag generation")
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
        start_time = time.time()
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=TAG_TEMPERATURE,
            max_tokens=TAG_MAX_TOKENS,
            operation="semantic_tags",
            entry_date=entries[0].date if entries else None
        )
        elapsed = time.time() - start_time

        # Parse tags from response (simplified logic)
        tags = []
        for line in response.split("\n"):
            # Remove # prefix if present and clean the tag
            tag = line.strip().lstrip("#").lower()
            
            # Validate tag length and content
            if MIN_TAG_LENGTH <= len(tag) <= MAX_TAG_LENGTH and tag:
                tags.append(tag)

        result_tags = tags[:max_tags]
        
        logger.info(
            f"Generated {len(result_tags)} semantic tags in {elapsed:.2f}s "
            f"from {len(entries)} entries"
        )
        
        return result_tags

    except RuntimeError as e:
        logger.warning(f"LLM tag generation failed for {len(entries)} entries - {e}")
        return []
