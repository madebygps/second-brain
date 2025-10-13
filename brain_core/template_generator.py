"""Generate AI prompts based on recent diary entries."""
from datetime import date
from typing import List
import logging
import time
from .entry_manager import DiaryEntry, EntryManager
from .llm_client import LLMClient
from .llm_analysis import _truncate_text
from .logging_config import log_operation_timing
from .constants import (
    DAILY_PROMPT_COUNT,
    WEEKLY_PROMPT_COUNT,
    PROMPT_CONTEXT_DAYS,
    WEEKLY_CONTEXT_DAYS,
    PROMPT_TEMPERATURE,
    PROMPT_MAX_TOKENS,
    WEEKLY_PROMPT_MAX_TOKENS,
    ENTRY_PREVIEW_LENGTH
)

logger = logging.getLogger(__name__)


def _parse_prompts_from_response(response: str, expected_count: int) -> List[str]:
    """Parse numbered prompts from LLM response.
    
    Args:
        response: Raw LLM response text
        expected_count: Expected number of prompts
        
    Returns:
        List of cleaned prompt strings
    """
    prompts = []
    for line in response.split("\n"):
        line = line.strip()
        # Match patterns like "1. Question here" or "1) Question here" or "- Question"
        if line and (line[0].isdigit() or line.startswith("-")):
            # Remove leading number/bullet and whitespace
            cleaned = line.lstrip("0123456789.-) ").strip()
            if cleaned:
                prompts.append(cleaned)
    
    # Return up to expected count
    return prompts[:expected_count] if prompts else []


def is_sunday(entry_date: date) -> bool:
    """Check if date is Sunday (weekday 6).
    
    Args:
        entry_date: Date to check
        
    Returns:
        True if Sunday, False otherwise
    """
    return entry_date.weekday() == 6


def generate_daily_prompts(
    recent_entries: List[DiaryEntry],
    llm_client: LLMClient,
    target_date: date
) -> List[str]:
    """Generate 3 daily reflection prompts based on recent entries.
    
    Uses LLM to analyze recent diary entries and create personalized,
    diverse reflection questions that reference specific past entries.
    
    Args:
        recent_entries: List of recent diary entries for context (typically 3 days)
        llm_client: LLM client for prompt generation
        target_date: The date for which prompts are being generated
        
    Returns:
        List of 3 reflection prompt strings with [[YYYY-MM-DD]] backlinks
    """
    if not recent_entries:
        return [
            "What are you thinking about today?",
            "What's on your mind?",
            "How are you feeling?"
        ]

    # Build context from recent entries
    context_parts = []
    for entry in recent_entries[:PROMPT_CONTEXT_DAYS]:
        date_str = entry.date.isoformat()
        preview = _truncate_text(entry.brain_dump, ENTRY_PREVIEW_LENGTH)
        if preview:
            context_parts.append(f"[[{date_str}]]: {preview}")

    context = "\n\n".join(context_parts)
    
    logger.debug(f"Generating daily prompts with {len(recent_entries)} recent entries")

    system_prompt = """You are a thoughtful journaling assistant. Generate 3 reflective questions
based on the user's recent diary entries. Questions should:
- MUST reference at least one specific entry using [[YYYY-MM-DD]] format in each question
- Build on themes, questions, or situations mentioned in the referenced entries
- Encourage deeper reflection
- Be personal and specific (not generic)
- Do NOT use emojis in your questions
- Use plain text only

CRITICAL: Each of the 3 questions MUST address DIFFERENT topics from the entries.
- Question 1: Focus on one theme/topic
- Question 2: Focus on a DIFFERENT theme/topic
- Question 3: Focus on yet ANOTHER distinct theme/topic

Do NOT make multiple questions about the same topic or event. Spread across the diversity of experiences mentioned.

IMPORTANT: Each question MUST include at least one [[YYYY-MM-DD]] backlink to show where the prompt came from.

Format each question on a new line, numbered 1-3. Be concise."""

    user_prompt = f"""Based on these recent diary entries, generate 3 thoughtful reflection prompts:

{context}

STEP 1: Scan ALL topics mentioned across the entries. List distinct themes like:
- Professional work (teaching, projects, sessions)
- Personal relationships (partner, family, friends, colleagues)
- Health & wellness (sleep, diet, exercise, mental health)
- Tools & systems (journaling, technology, workflows)
- Personal growth (habits, skills, self-improvement)
- Hobbies & interests (books, music, activities)

STEP 2: Select 3 COMPLETELY DIFFERENT themes from Step 1.
STEP 3: Generate 1 question for EACH of those 3 different themes.

Example of GOOD diversity:
- Q1: About teaching/work [[date]]
- Q2: About relationship with partner [[date]]
- Q3: About sleep/health habits [[date]]

Example of BAD (too similar):
- Q1: About Python sessions [[date]]
- Q2: About Spanish office hours [[date]]  ← Same topic area!
- Q3: About teaching community [[date]]  ← Same topic area!

Each prompt MUST include at least one [[YYYY-MM-DD]] backlink."""

    try:
        start_time = time.time()
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.9,  # Higher temperature for diversity
            max_tokens=PROMPT_MAX_TOKENS,
            operation="daily_prompts",
            entry_date=target_date.strftime("%Y-%m-%d")
        )
        elapsed = time.time() - start_time

        # Parse prompts from response
        prompts = _parse_prompts_from_response(response, DAILY_PROMPT_COUNT)

        # Ensure we have exactly the right number of prompts
        if len(prompts) >= DAILY_PROMPT_COUNT:
            logger.debug(f"Generated {DAILY_PROMPT_COUNT} daily prompts in {elapsed:.2f}s")
            return prompts[:DAILY_PROMPT_COUNT]
        elif prompts:
            # If we got some but not enough, pad with generic ones
            while len(prompts) < DAILY_PROMPT_COUNT:
                prompts.append("What else is on your mind?")
            logger.debug(f"Generated {len(prompts)} daily prompts (padded) in {elapsed:.2f}s")
            return prompts
        else:
            # Fall back to generic prompts if parsing failed
            logger.debug(f"Failed to parse LLM response in {elapsed:.2f}s, using generic prompts")
            return [
                "What stood out to you recently?",
                "What are you thinking about?",
                "How are you feeling about things?"
            ]

    except RuntimeError as e:
        # Fall back to generic prompts if LLM fails
        logger.warning("Failed to generate prompts via LLM: %s", e)
        return [
            "What stood out to you recently?",
            "What are you thinking about?",
            "How are you feeling about things?"
        ]


def generate_weekly_prompts(
    recent_entries: List[DiaryEntry],
    llm_client: LLMClient,
    target_date: date
) -> List[str]:
    """Generate 5 weekly reflection prompts based on past week.
    
    Uses LLM to analyze a full week of diary entries and create broader
    reflection questions covering diverse life areas.
    
    Args:
        recent_entries: List of diary entries from past week (typically 7 days)
        llm_client: LLM client for prompt generation
        
    Returns:
        List of 5 weekly reflection prompt strings with [[YYYY-MM-DD]] backlinks
    """
    if not recent_entries:
        return [
            "What were the highlights of your week?",
            "What challenged you this week?",
            "What did you learn?",
            "What are you grateful for?",
            "What do you want to focus on next week?"
        ]

    # Build context from weekly entries
    context_parts = []
    for entry in recent_entries[:WEEKLY_CONTEXT_DAYS]:
        date_str = entry.date.isoformat()
        preview = _truncate_text(entry.brain_dump, ENTRY_PREVIEW_LENGTH)
        if preview:
            context_parts.append(f"[[{date_str}]]: {preview}")

    context = "\n\n".join(context_parts)
    
    logger.debug(f"Generating weekly prompts with {len(recent_entries)} recent entries")

    system_prompt = """You are a thoughtful journaling assistant. Generate 5 weekly reflection questions
based on the user's past week of diary entries. Questions should:
- MUST reference at least one specific entry using [[YYYY-MM-DD]] format in each question
- Help identify patterns and themes across the week
- Encourage broader reflection on progress and direction
- Be personal and specific (not generic)
- Do NOT use emojis in your questions
- Use plain text only

CRITICAL: Each of the 5 questions MUST address DIFFERENT topics/themes from the week.
- Question 1: Focus on one theme/area
- Question 2: Focus on a DIFFERENT theme/area
- Question 3: Focus on yet ANOTHER distinct theme/area
- Question 4: Focus on a fourth distinct theme/area
- Question 5: Focus on a fifth distinct theme/area

Do NOT make multiple questions about the same topic. Maximize diversity across different aspects of the week.

IMPORTANT: Each question MUST include at least one [[YYYY-MM-DD]] backlink to show where the prompt came from.

Format each question on a new line, numbered 1-5. Be concise."""

    user_prompt = f"""Based on this past week of diary entries, generate 5 weekly reflection prompts:

{context}

Generate 5 numbered prompts about DIFFERENT aspects of the week. Each prompt MUST:
1. Address a distinct theme/area (work, relationships, health, personal growth, etc.)
2. Include at least one [[YYYY-MM-DD]] backlink to reference where the prompt came from

Ensure maximum diversity - cover different life areas, NOT the same topic 5 times."""

    try:
        start_time = time.time()
        response = llm_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=PROMPT_TEMPERATURE,
            max_tokens=WEEKLY_PROMPT_MAX_TOKENS,
            operation="weekly_prompts"
        )
        elapsed = time.time() - start_time

        # Parse prompts from response
        prompts = _parse_prompts_from_response(response, WEEKLY_PROMPT_COUNT)

        # Ensure we have exactly the right number of prompts
        if len(prompts) >= WEEKLY_PROMPT_COUNT:
            logger.debug(f"Generated {WEEKLY_PROMPT_COUNT} weekly prompts in {elapsed:.2f}s")
            return prompts[:WEEKLY_PROMPT_COUNT]
        elif prompts:
            while len(prompts) < WEEKLY_PROMPT_COUNT:
                prompts.append("What else comes to mind?")
            logger.debug(f"Generated {len(prompts)} weekly prompts (padded) in {elapsed:.2f}s")
            return prompts
        else:
            logger.debug(f"Failed to parse LLM response in {elapsed:.2f}s, using generic prompts")
            return [
                "What were the key themes this week?",
                "What did you accomplish?",
                "What challenged you?",
                "What are you grateful for?",
                "What's ahead for next week?"
            ]

    except RuntimeError as e:
        logger.warning("Failed to generate weekly prompts via LLM: %s", e)
        return [
            "What were the key themes this week?",
            "What did you accomplish?",
            "What challenged you?",
            "What are you grateful for?",
            "What's ahead for next week?"
        ]


def generate_prompts_for_date(
    target_date: date,
    entry_manager: EntryManager,
    llm_client: LLMClient
) -> List[str]:
    """Generate prompts for a specific date based on context.
    
    Orchestrator function that determines whether to generate daily (3 prompts)
    or weekly (5 prompts) based on whether target_date is Sunday.
    
    Args:
        target_date: Date to generate prompts for
        entry_manager: Manager for reading past diary entries
        llm_client: LLM client for prompt generation
        
    Returns:
        List of 3 prompts (daily) or 5 prompts (weekly) with backlinks
    """
    # Get past calendar days (not last N entries)
    past_dates = entry_manager.get_past_calendar_days(target_date, PROMPT_CONTEXT_DAYS)
    recent_entries = entry_manager.get_entries_for_dates(past_dates)

    # Sunday gets weekly prompts, other days get daily prompts
    if is_sunday(target_date):
        # For Sunday, look back for weekly context
        past_week_dates = entry_manager.get_past_calendar_days(target_date, WEEKLY_CONTEXT_DAYS)
        week_entries = entry_manager.get_entries_for_dates(past_week_dates)
        return generate_weekly_prompts(week_entries, llm_client, target_date)
    else:
        return generate_daily_prompts(recent_entries, llm_client, target_date)
