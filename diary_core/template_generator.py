"""Generate AI prompts based on recent diary entries."""
from datetime import date
from typing import List
import re
from .entry_manager import DiaryEntry, EntryManager
from .ollama_client import OllamaClient
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


def remove_emojis(text: str) -> str:
    """Remove emojis from text."""
    # Emoji pattern covering most common emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text).strip()


def is_sunday(entry_date: date) -> bool:
    """Check if date is Sunday (weekday 6)."""
    return entry_date.weekday() == 6


def generate_daily_prompts(
    recent_entries: List[DiaryEntry],
    ollama_client: OllamaClient
) -> List[str]:
    """Generate 3 daily reflection prompts based on recent entries."""
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
        preview = entry.brain_dump[:ENTRY_PREVIEW_LENGTH] if len(entry.brain_dump) > ENTRY_PREVIEW_LENGTH else entry.brain_dump
        if preview:
            context_parts.append(f"[[{date_str}]]: {preview}")

    context = "\n\n".join(context_parts)

    system_prompt = """You are a thoughtful journaling assistant. Generate 3 reflective questions
based on the user's recent diary entries. Questions should:
- MUST reference at least one specific entry using [[YYYY-MM-DD]] format in each question
- Build on themes, questions, or situations mentioned in the referenced entries
- Encourage deeper reflection
- Be personal and specific (not generic)
- Do NOT use emojis in your questions
- Use plain text only

IMPORTANT: Each question MUST include at least one [[YYYY-MM-DD]] backlink to show where the prompt came from.

Format each question on a new line, numbered 1-3. Be concise."""

    user_prompt = f"""Based on these recent diary entries, generate 3 thoughtful reflection prompts:

{context}

Generate 3 numbered prompts. Each prompt MUST include at least one [[YYYY-MM-DD]] backlink to reference where the prompt came from."""

    try:
        response = ollama_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=PROMPT_TEMPERATURE,
            max_tokens=PROMPT_MAX_TOKENS
        )

        # Parse prompts from response
        prompts = []
        for line in response.split("\n"):
            line = line.strip()
            # Match patterns like "1. Question here" or "1) Question here"
            if line and (line[0].isdigit() or line.startswith("-")):
                # Remove leading number/bullet and whitespace
                cleaned = line.lstrip("0123456789.-) ").strip()
                # Remove any emojis
                cleaned = remove_emojis(cleaned)
                if cleaned:
                    prompts.append(cleaned)

        # Ensure we have exactly the right number of prompts
        if len(prompts) >= DAILY_PROMPT_COUNT:
            return prompts[:DAILY_PROMPT_COUNT]
        elif prompts:
            # If we got some but not enough, pad with generic ones
            while len(prompts) < DAILY_PROMPT_COUNT:
                prompts.append("What else is on your mind?")
            return prompts
        else:
            # Fall back to generic prompts if parsing failed
            return [
                "What stood out to you recently?",
                "What are you thinking about?",
                "How are you feeling about things?"
            ]

    except RuntimeError as e:
        # Fall back to generic prompts if LLM fails
        print(f"Warning: Failed to generate prompts via LLM: {e}")
        return [
            "What stood out to you recently?",
            "What are you thinking about?",
            "How are you feeling about things?"
        ]


def generate_weekly_prompts(
    recent_entries: List[DiaryEntry],
    ollama_client: OllamaClient
) -> List[str]:
    """Generate 5 weekly reflection prompts based on past week."""
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
        preview = entry.brain_dump[:ENTRY_PREVIEW_LENGTH] if len(entry.brain_dump) > ENTRY_PREVIEW_LENGTH else entry.brain_dump
        if preview:
            context_parts.append(f"[[{date_str}]]: {preview}")

    context = "\n\n".join(context_parts)

    system_prompt = """You are a thoughtful journaling assistant. Generate 5 weekly reflection questions
based on the user's past week of diary entries. Questions should:
- MUST reference at least one specific entry using [[YYYY-MM-DD]] format in each question
- Help identify patterns and themes across the week
- Encourage broader reflection on progress and direction
- Be personal and specific (not generic)
- Do NOT use emojis in your questions
- Use plain text only

IMPORTANT: Each question MUST include at least one [[YYYY-MM-DD]] backlink to show where the prompt came from.

Format each question on a new line, numbered 1-5. Be concise."""

    user_prompt = f"""Based on this past week of diary entries, generate 5 weekly reflection prompts:

{context}

Generate 5 numbered prompts that help reflect on patterns, progress, and direction. Each prompt MUST include at least one [[YYYY-MM-DD]] backlink to reference where the prompt came from."""

    try:
        response = ollama_client.generate_sync(
            prompt=user_prompt,
            system=system_prompt,
            temperature=PROMPT_TEMPERATURE,
            max_tokens=WEEKLY_PROMPT_MAX_TOKENS
        )

        # Parse prompts from response
        prompts = []
        for line in response.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                cleaned = line.lstrip("0123456789.-) ").strip()
                # Remove any emojis
                cleaned = remove_emojis(cleaned)
                if cleaned:
                    prompts.append(cleaned)

        # Ensure we have exactly the right number of prompts
        if len(prompts) >= WEEKLY_PROMPT_COUNT:
            return prompts[:WEEKLY_PROMPT_COUNT]
        elif prompts:
            while len(prompts) < WEEKLY_PROMPT_COUNT:
                prompts.append("What else comes to mind?")
            return prompts
        else:
            return [
                "What were the key themes this week?",
                "What did you accomplish?",
                "What challenged you?",
                "What are you grateful for?",
                "What's ahead for next week?"
            ]

    except RuntimeError as e:
        print(f"Warning: Failed to generate weekly prompts via LLM: {e}")
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
    ollama_client: OllamaClient
) -> List[str]:
    """Generate prompts for a specific date based on context."""
    # Get past calendar days (not last N entries)
    past_dates = entry_manager.get_past_calendar_days(target_date, PROMPT_CONTEXT_DAYS)
    recent_entries = entry_manager.get_entries_for_dates(past_dates)

    # Sunday gets weekly prompts, other days get daily prompts
    if is_sunday(target_date):
        # For Sunday, look back for weekly context
        past_week_dates = entry_manager.get_past_calendar_days(target_date, WEEKLY_CONTEXT_DAYS)
        week_entries = entry_manager.get_entries_for_dates(past_week_dates)
        return generate_weekly_prompts(week_entries, ollama_client)
    else:
        return generate_daily_prompts(recent_entries, ollama_client)
