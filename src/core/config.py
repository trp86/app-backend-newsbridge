"""Configuration management using Pydantic settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.schemas import RSSSource


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Google Gemini API
    gemini_api_key: str = Field(description="Google Gemini API key")
    gemini_summarization_model: str = Field(
        default="gemini-2.5-flash",
        description="Model for summarization",
    )
    gemini_translation_model: str = Field(
        default="gemini-1.5-flash",
        description="Model for translation",
    )

    # Telegram
    telegram_bot_token: str = Field(description="Telegram bot token from BotFather")
    telegram_channel_id: str = Field(description="Telegram channel ID (e.g., @channelname)")

    # Database
    database_url: str = Field(
        default="",
        description="Database URL (Neon Postgres or SQLite). Example: postgresql://user:pass@host/db",
    )
    database_path: Path = Field(
        default=Path("data/brief.db"),
        description="SQLite database path (fallback if database_url not set)",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or console")

    # Scheduling
    daily_publish_time: str = Field(
        default="06:00",
        description="Daily publish time (UTC, HH:MM format)",
    )

    # Retry settings
    max_retries_per_model: int = Field(default=2, description="Max retries per model")
    request_timeout_seconds: int = Field(default=30, description="API request timeout")

    # Content filtering
    min_quality_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for stories",
    )
    top_stories_count: int = Field(default=5, description="Number of stories per brief")


def get_rss_sources() -> list[RSSSource]:
    """Get configured RSS sources - Milestone 2: German news focus (hybrid).

    Mix of German language and English sources representing what Germans read daily.
    German articles require translation to English before summarization.

    Returns:
        List of RSS source configurations
    """
    return [
        # German language sources (require DE→EN translation)
        RSSSource(
            name="Tagesschau",
            url="https://www.tagesschau.de/xml/rss2/",
            priority=1,
            expected_articles=30,
            enabled=True,
        ),
        RSSSource(
            name="Süddeutsche Zeitung",
            url="https://www.sueddeutsche.de/news/rss",
            priority=1,
            expected_articles=25,
            enabled=True,
        ),
        # English sources (direct processing)
        RSSSource(
            name="Der Spiegel International",
            url="https://www.spiegel.de/international/index.rss",
            priority=1,
            expected_articles=15,
            enabled=True,
        ),
        RSSSource(
            name="Deutsche Welle World",
            url="https://rss.dw.com/xml/rss-en-world",
            priority=1,
            expected_articles=25,
            enabled=True,
        ),
        RSSSource(
            name="Handelsblatt Global",
            url="https://www.handelsblatt.com/contentexport/feed/top-themen",
            priority=1,
            expected_articles=20,
            enabled=True,
        ),
    ]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance loaded from environment
    """
    return Settings()
