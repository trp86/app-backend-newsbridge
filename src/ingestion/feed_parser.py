"""RSS feed entry parsing."""

from datetime import datetime

import feedparser
import structlog
from pydantic import HttpUrl

from src.core.schemas import RawArticle, SourceType
from src.ingestion.rss_collector import generate_article_id, generate_content_hash

logger = structlog.get_logger()


def parse_published_date(entry: feedparser.FeedParserDict) -> datetime:
    """Extract publication date from feed entry.

    Args:
        entry: Feed entry dictionary

    Returns:
        Publication datetime (or current time if not found)
    """
    # Try different date fields
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        return datetime(*entry.published_parsed[:6])

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        return datetime(*entry.updated_parsed[:6])

    # Fallback to current time
    logger.warning(
        "entry.no_date",
        title=getattr(entry, "title", "unknown"),
        fallback="now",
    )
    return datetime.now()


def extract_content(entry: feedparser.FeedParserDict) -> str:
    """Extract article content from feed entry.

    Args:
        entry: Feed entry dictionary

    Returns:
        Article content text (empty string if not found)
    """
    # Try different content fields
    if hasattr(entry, "content") and entry.content:
        return entry.content[0].value

    if hasattr(entry, "summary") and entry.summary:
        return entry.summary

    if hasattr(entry, "description") and entry.description:
        return entry.description

    logger.warning(
        "entry.no_content",
        title=getattr(entry, "title", "unknown"),
    )
    return ""


def parse_feed_entry(entry: feedparser.FeedParserDict, source_name: str) -> RawArticle:
    """Parse RSS feed entry into RawArticle.

    Args:
        entry: Feed entry from feedparser
        source_name: Name of the RSS source

    Returns:
        Parsed RawArticle

    Raises:
        ValueError: If required fields are missing
    """
    # Extract required fields
    if not hasattr(entry, "link"):
        raise ValueError("Entry missing 'link' field")

    if not hasattr(entry, "title"):
        raise ValueError("Entry missing 'title' field")

    source_url = entry.link
    title = entry.title
    content = extract_content(entry)
    published_at = parse_published_date(entry)
    fetched_at = datetime.now()

    # Generate IDs and hashes
    article_id = generate_article_id(source_url, published_at)
    content_hash = generate_content_hash(content)

    article = RawArticle(
        id=article_id,
        source_url=HttpUrl(source_url),
        source_name=source_name,
        source_type=SourceType.RSS,
        title=title,
        content=content,
        published_at=published_at,
        fetched_at=fetched_at,
        content_hash=content_hash,
        is_duplicate=False,
    )

    logger.debug(
        "entry.parsed",
        article_id=article_id,
        source=source_name,
        title=title[:50],
    )

    return article
