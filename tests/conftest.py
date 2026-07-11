"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables."""
    os.environ["OPENROUTER_API_KEY"] = "test-key-12345"
    os.environ["TELEGRAM_BOT_TOKEN"] = "test-bot-token"
    os.environ["TELEGRAM_CHANNEL_ID"] = "@test_channel"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["LOG_FORMAT"] = "console"


@pytest.fixture
def temp_database():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = Path(tmp.name)

    os.environ["DATABASE_PATH"] = str(db_path)

    # Clear settings cache to pick up new DATABASE_PATH
    from src.core.config import get_settings
    get_settings.cache_clear()

    yield db_path

    # Cleanup
    if db_path.exists():
        db_path.unlink()

    # Clear cache again after test
    get_settings.cache_clear()
