"""Tests for feed parser."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from src.ingestion.feed_parser import (
    extract_content,
    parse_feed_entry,
    parse_published_date,
)


def test_parse_published_date_with_published_parsed():
    """Test date parsing from published_parsed field."""
    entry = Mock()
    entry.published_parsed = (2026, 7, 4, 12, 30, 0)

    date = parse_published_date(entry)

    assert date == datetime(2026, 7, 4, 12, 30, 0)


def test_parse_published_date_with_updated_parsed():
    """Test date parsing from updated_parsed field."""
    entry = Mock()
    entry.published_parsed = None
    entry.updated_parsed = (2026, 7, 4, 10, 0, 0)

    date = parse_published_date(entry)

    assert date == datetime(2026, 7, 4, 10, 0, 0)


def test_parse_published_date_fallback():
    """Test date parsing falls back to current time."""
    entry = Mock()
    entry.published_parsed = None
    entry.updated_parsed = None
    entry.title = "Test Article"

    before = datetime.now()
    date = parse_published_date(entry)
    after = datetime.now()

    assert before <= date <= after


def test_extract_content_from_content_field():
    """Test content extraction from content field."""
    entry = Mock()
    entry.content = [Mock(value="Test content from content field")]

    content = extract_content(entry)

    assert content == "Test content from content field"


def test_extract_content_from_summary():
    """Test content extraction from summary field."""
    entry = Mock()
    entry.content = None
    entry.summary = "Test content from summary"

    content = extract_content(entry)

    assert content == "Test content from summary"


def test_extract_content_from_description():
    """Test content extraction from description field."""
    entry = Mock()
    entry.content = None
    entry.summary = None
    entry.description = "Test content from description"

    content = extract_content(entry)

    assert content == "Test content from description"


def test_extract_content_empty():
    """Test content extraction returns empty string when no content."""
    entry = Mock()
    entry.content = None
    entry.summary = None
    entry.description = None
    entry.title = "Test"

    content = extract_content(entry)

    assert content == ""


def test_parse_feed_entry_valid():
    """Test parsing valid feed entry."""
    entry = Mock()
    entry.link = "https://example.com/article"
    entry.title = "Test Article"
    entry.content = None  # Explicitly set to None so it checks summary
    entry.summary = "Test content"
    entry.published_parsed = (2026, 7, 4, 12, 0, 0)

    article = parse_feed_entry(entry, "Test Source")

    assert article.title == "Test Article"
    assert article.source_name == "Test Source"
    assert str(article.source_url) == "https://example.com/article"
    assert article.content == "Test content"
    assert article.published_at == datetime(2026, 7, 4, 12, 0, 0)
    assert article.is_duplicate is False


def test_parse_feed_entry_missing_link():
    """Test parsing fails without link."""
    entry = Mock()
    entry.title = "Test"
    del entry.link

    with pytest.raises(ValueError, match="missing 'link'"):
        parse_feed_entry(entry, "Test Source")


def test_parse_feed_entry_missing_title():
    """Test parsing fails without title."""
    entry = Mock()
    entry.link = "https://example.com/article"
    del entry.title

    with pytest.raises(ValueError, match="missing 'title'"):
        parse_feed_entry(entry, "Test Source")
