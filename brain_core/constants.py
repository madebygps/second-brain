"""Constants used throughout the diary system."""

# Entry content thresholds
MIN_SUBSTANTIAL_CONTENT_CHARS = 1

# LLM Analysis limits
MAX_SEMANTIC_LINK_CANDIDATES = 20  # Max number of candidate entries to compare
MAX_SEMANTIC_LINKS = 5  # Max links to include in final results
MAX_TOPIC_TAGS = 5  # Max topic tags to generate per entry
MAX_ENTRIES_FOR_TAG_CONTEXT = 5  # Max entries to analyze for tag generation

# Preview lengths for LLM context (characters)
ENTRY_PREVIEW_LENGTH = 400  # For candidate entries in lists (shorter for token efficiency)
TARGET_PREVIEW_LENGTH = 500  # For main entry being analyzed (longer for better matching)

# Analysis parameters 
DEFAULT_THEMES_COUNT = 10
MEMORY_TRACE_TOP_THEMES = 15
TOP_CONNECTED_ENTRIES = 5

# LLM parameters
LLM_TIMEOUT_SECONDS = 300.0  # 5 minutes
LLM_CONNECTION_CHECK_TIMEOUT = 5.0

# Prompt generation
DAILY_PROMPT_COUNT = 1
WEEKLY_PROMPT_COUNT = 5
PROMPT_CONTEXT_DAYS = 3
WEEKLY_CONTEXT_DAYS = 7
PROMPT_TEMPERATURE = 0.8
PROMPT_MAX_TOKENS = 300
WEEKLY_PROMPT_MAX_TOKENS = 500

# Semantic analysis
MIN_CONTENT_FOR_ENTITY_EXTRACTION = 50  # Minimum chars needed for entity extraction
ENTITY_EXTRACTION_MAX_TOKENS = 200  # Max tokens for entity extraction response
SEMANTIC_BACKLINKS_MAX_TOKENS = 400  # Max tokens for semantic backlinks response
SEMANTIC_TEMPERATURE = 0.3
SEMANTIC_MAX_TOKENS = 200  # Max tokens for theme extraction in analysis.py
TAG_TEMPERATURE = 0.5
TAG_MAX_TOKENS = 100

# Tag validation (used by generate_semantic_tags in llm_analysis.py)
MIN_TAG_LENGTH = 3
MAX_TAG_LENGTH = 15

# Context lookback
PAST_ENTRIES_LOOKBACK_DAYS = 90
