"""Centralized logging configuration for the brain system."""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    console_format: str = "simple",
    enable_file_logging: bool = False,
    use_config: bool = True,
) -> None:
    """Configure centralized logging for the brain system.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file. If None, logs only to console.
        console_format: Console log format (simple, detailed, json)
        enable_file_logging: Whether to enable file logging
        use_config: If True, override parameters with values from config/env vars
    """
    # Override with config values if requested
    if use_config:
        try:
            from .config import get_config

            config = get_config()
            level = config.log_level
            if config.log_file:
                log_file = Path(config.log_file)
                enable_file_logging = True
        except Exception:
            # If config loading fails, use provided defaults
            pass

    # Determine log level
    if level is None:
        level = os.getenv("LOG_LEVEL", "WARNING").upper()

    log_level = getattr(logging, level, logging.WARNING)

    # Create file formatter (Rich handles console formatting)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Configure root logger
    root_logger = logging.getLogger()

    # If file logging is enabled, root logger should capture everything (DEBUG)
    # so file gets full details. Console handler will filter based on user preference.
    if enable_file_logging:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler with Rich for prettier output
    console = Console(stderr=True)
    console_handler = RichHandler(
        console=console,
        show_time=False,
        show_path=False,
        markup=True,
        rich_tracebacks=True,
        tracebacks_show_locals=False,
    )
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # File handler (if enabled) with rotation
    if enable_file_logging:
        if log_file is None:
            log_dir = Path.home() / ".brain" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "brain.log"
        else:
            # Expand ~ in path and ensure parent directory exists
            log_file = Path(log_file).expanduser()
            log_file.parent.mkdir(parents=True, exist_ok=True)

        # Rotating file handler: max 10MB per file, keep 5 backup files
        # This means max ~50MB of logs total (10MB current + 5x10MB backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,  # Keep 5 old files (brain.log.1, brain.log.2, etc.)
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)  # File always captures everything
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Configure specific loggers to prevent double logging
    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def enable_debug_logging() -> None:
    """Enable debug logging for all brain modules."""
    logging.getLogger().setLevel(logging.DEBUG)
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.DEBUG)


def enable_verbose_logging() -> None:
    """Enable verbose (INFO) logging for all brain modules."""
    logging.getLogger().setLevel(logging.INFO)
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(logging.INFO)


def log_operation_timing(operation: str, elapsed_seconds: float, **kwargs) -> None:
    """Log operation timing with consistent format.

    Args:
        operation: Name of the operation
        elapsed_seconds: Time taken in seconds
        **kwargs: Additional context (tokens, entries, etc.)
    """
    logger = get_logger("brain.timing")

    context_parts = []
    for key, value in kwargs.items():
        context_parts.append(f"{key}={value}")

    context_str = f" ({', '.join(context_parts)})" if context_parts else ""
    logger.info(f"{operation} completed in {elapsed_seconds:.2f}s{context_str}")


def log_llm_call(
    operation: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    elapsed_seconds: float,
    cost_estimate: float,
) -> None:
    """Log LLM call details with consistent format.

    Args:
        operation: Type of operation (backlinks, tags, etc.)
        model: Model used
        prompt_tokens: Input token count
        completion_tokens: Output token count
        total_tokens: Total token count
        elapsed_seconds: Time taken
        cost_estimate: Estimated cost in USD
    """
    logger = get_logger("brain.llm")
    logger.debug(
        f"LLM {operation}: {model} | "
        f"{prompt_tokens}+{completion_tokens}={total_tokens} tokens | "
        f"{elapsed_seconds:.2f}s | ${cost_estimate:.4f}"
    )
