"""Tests for configuration management."""

import pytest

from src.core.config import get_rss_sources, get_settings


def test_get_settings(test_env):
    """Test settings loaded from environment."""
    settings = get_settings()
    assert settings.openrouter_api_key == "test-key-12345"
    assert settings.telegram_bot_token == "test-bot-token"
    assert settings.telegram_channel_id == "@test_channel"
    assert settings.log_level == "DEBUG"
    assert settings.top_stories_count == 5


def test_get_settings_defaults(test_env):
    """Test settings have correct defaults."""
    settings = get_settings()
    assert settings.openrouter_summarization_model == "google/gemini-flash-1.5"
    assert settings.openrouter_translation_model == "google/gemini-pro-1.5"
    assert settings.max_retries_per_model == 2
    assert settings.min_quality_score == 0.7
    assert settings.daily_publish_time == "06:00"


def test_get_rss_sources():
    """Test RSS sources configuration."""
    sources = get_rss_sources()

    assert len(sources) == 6

    # Check priority 1 sources
    priority_1 = [s for s in sources if s.priority == 1]
    assert len(priority_1) == 4
    assert any(s.name == "Reuters World" for s in priority_1)
    assert any(s.name == "BBC World" for s in priority_1)

    # Check priority 2 sources
    priority_2 = [s for s in sources if s.priority == 2]
    assert len(priority_2) == 2
    assert any(s.name == "NASA Breaking" for s in priority_2)


def test_rss_sources_have_valid_urls():
    """Test all RSS sources have valid HTTPS URLs."""
    sources = get_rss_sources()

    for source in sources:
        assert source.url.scheme in ["http", "https"]
        assert source.expected_articles > 0
        assert source.enabled is True
