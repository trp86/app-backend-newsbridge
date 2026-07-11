"""RSS feed collection from configured sources."""

import hashlib
from datetime import datetime

import feedparser
import httpx
import structlog

from src.core.config import get_rss_sources, get_settings
from src.core.schemas import RawArticle, SourceType

logger = structlog.get_logger()


def fetch_feed(url: str, timeout: int = 30) -> feedparser.FeedParserDict:
    """Fetch RSS feed from URL.

    Args:
        url: RSS feed URL
        timeout: Request timeout in seconds

    Returns:
        Parsed feed dictionary

    Raises:
        httpx.HTTPError: If feed fetch fails
    """
    logger.info("feed.fetch", url=url)

    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()

    feed = feedparser.parse(response.content)

    if feed.bozo:
        logger.warning(
            "feed.parse_error",
            url=url,
            error=str(feed.bozo_exception),
        )

    logger.info(
        "feed.fetched",
        url=url,
        entries=len(feed.entries),
    )

    return feed


def generate_article_id(source_url: str, published_at: datetime) -> str:
    """Generate unique article ID from URL and publish date.

    Args:
        source_url: Article URL
        published_at: Publication datetime

    Returns:
        SHA256 hash (first 16 characters)
    """
    content = f"{source_url}:{published_at.isoformat()}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def generate_content_hash(content: str) -> str:
    """Generate content hash for deduplication.

    Args:
        content: Article content text

    Returns:
        SHA256 hash
    """
    normalized = content.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


def collect_articles() -> list[RawArticle]:
    """Collect articles from all configured RSS sources.

    Returns:
        List of raw articles (not deduplicated)

    Example:
        articles = collect_articles()
        logger.info(f"Collected {len(articles)} articles")
    """
    from src.ingestion.feed_parser import parse_feed_entry

    settings = get_settings()
    sources = get_rss_sources()
    all_articles: list[RawArticle] = []

    logger.info("collection.started", source_count=len(sources))

    for source in sources:
        if not source.enabled:
            logger.debug("source.skipped", name=source.name, reason="disabled")
            continue

        try:
            feed = fetch_feed(str(source.url), timeout=settings.request_timeout_seconds)

            for entry in feed.entries:
                try:
                    article = parse_feed_entry(entry, source.name)
                    all_articles.append(article)
                except Exception as e:
                    logger.error(
                        "entry.parse_failed",
                        source=source.name,
                        error=str(e),
                        entry_title=getattr(entry, "title", "unknown"),
                    )
                    continue

            logger.info(
                "source.collected",
                name=source.name,
                articles=len([a for a in all_articles if a.source_name == source.name]),
            )

        except Exception as e:
            logger.error(
                "source.fetch_failed",
                name=source.name,
                url=str(source.url),
                error=str(e),
            )
            continue

    logger.info("collection.completed", total_articles=len(all_articles))

    return all_articles
