"""Configuration management for diary system."""
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import os


class Config:
    """Configuration loaded from .env file."""

    def __init__(self, env_file: Optional[Path] = None):
        """Load configuration from .env file."""
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Required paths
        diary_path = os.getenv("DIARY_PATH")
        if not diary_path:
            raise ValueError("DIARY_PATH must be set in .env")

        planner_path = os.getenv("PLANNER_PATH")
        if not planner_path:
            raise ValueError("PLANNER_PATH must be set in .env")

        self.diary_path = Path(diary_path)
        self.planner_path = Path(planner_path)

        # Validate paths exist
        if not self.diary_path.exists():
            raise ValueError(f"DIARY_PATH does not exist: {self.diary_path}")
        if not self.planner_path.exists():
            raise ValueError(f"PLANNER_PATH does not exist: {self.planner_path}")

        # Optional configuration
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:latest")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

        # Daemon configuration
        self.daemon_auto_link_time = os.getenv("DAEMON_AUTO_LINK_TIME", "23:00")
        self.daemon_weekly_analysis = os.getenv("DAEMON_WEEKLY_ANALYSIS", "true").lower() == "true"
        self.daemon_refresh_days = int(os.getenv("DAEMON_REFRESH_DAYS", "30"))


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get or create global config instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config) -> None:
    """Set global config instance (for testing)."""
    global _config
    _config = config
