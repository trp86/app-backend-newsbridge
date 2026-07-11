"""Tests for RSS collector."""

from datetime import datetime
from unittest.mock import Mock, patch

import feedparser
import pytest

from src.ingestion.rss_collector import (
    collect_articles,
    fetch_feed,
    generate_article_id,
    generate_content_hash,
)


def test_generate_article_id():
    """Test article ID generation is consistent."""
    url = "https://example.com/article"
    date = datetime(2026, 7, 4, 12, 0, 0)

    id1 = generate_article_id(url, date)
    id2 = generate_article_id(url, date)

    assert id1 == id2
    assert len(id1) == 16
    assert isinstance(id1, str)


def test_generate_article_id_different_inputs():
    """Test different inputs generate different IDs."""
    url1 = "https://example.com/article1"
    url2 = "https://example.com/article2"
    date = datetime(2026, 7, 4, 12, 0, 0)

    id1 = generate_article_id(url1, date)
    id2 = generate_article_id(url2, date)

    assert id1 != id2


def test_generate_content_hash():
    """Test content hash generation."""
    content = "This is test content"

    hash1 = generate_content_hash(content)
    hash2 = generate_content_hash(content)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256 hex length


def test_generate_content_hash_normalization():
    """Test content hash normalizes whitespace and case."""
    hash1 = generate_content_hash("Test Content")
    hash2 = generate_content_hash("test content")
    hash3 = generate_content_hash("  test content  ")

    assert hash1 == hash2 == hash3


@patch("src.ingestion.rss_collector.httpx.get")
def test_fetch_feed_success(mock_get):
    """Test successful feed fetch."""
    # Mock RSS feed XML
    mock_xml = """<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>Test Feed</title>
            <item>
                <title>Test Article</title>
                <link>https://example.com/article</link>
                <description>Test content</description>
            </item>
        </channel>
    </rss>
    """

    mock_response = Mock()
    mock_response.content = mock_xml.encode()
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    feed = fetch_feed("https://example.com/rss")

    assert len(feed.entries) == 1
    assert feed.entries[0].title == "Test Article"


@patch("src.ingestion.rss_collector.httpx.get")
def test_fetch_feed_http_error(mock_get):
    """Test feed fetch with HTTP error."""
    import httpx

    mock_get.side_effect = httpx.HTTPError("404 Not Found")

    with pytest.raises(httpx.HTTPError):
        fetch_feed("https://example.com/rss")
