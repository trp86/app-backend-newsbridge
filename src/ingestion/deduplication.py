"""Article deduplication logic."""

import structlog

from src.core.database import get_db_connection, get_placeholder, get_scalar

logger = structlog.get_logger()


def is_duplicate(content_hash: str) -> bool:
    """Check if article with given content hash already exists in database.

    Args:
        content_hash: SHA256 hash of article content

    Returns:
        True if article exists in database, False otherwise

    Example:
        if is_duplicate(article.content_hash):
            logger.info("Skipping duplicate article")
            continue
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        placeholder = get_placeholder()
        cursor.execute(
            f"SELECT COUNT(*) as count FROM articles WHERE content_hash = {placeholder}",
            (content_hash,),
        )
        result = cursor.fetchone()
        count = get_scalar(result, "count")

    is_dup = count > 0

    if is_dup:
        logger.debug("deduplication.duplicate_found", content_hash=content_hash[:16])

    return is_dup


def mark_duplicates(articles: list) -> tuple[list, list]:
    """Mark duplicate articles in a list.

    Args:
        articles: List of RawArticle objects

    Returns:
        Tuple of (unique_articles, duplicate_articles)

    Example:
        unique, duplicates = mark_duplicates(articles)
        logger.info(f"Found {len(unique)} unique, {len(duplicates)} duplicates")
    """
    unique = []
    duplicates = []
    seen_hashes = set()

    for article in articles:
        # Check against database
        if is_duplicate(article.content_hash):
            article.is_duplicate = True
            duplicates.append(article)
            logger.debug(
                "deduplication.db_duplicate",
                article_id=article.id,
                title=article.title[:50],
            )
            continue

        # Check against current batch
        if article.content_hash in seen_hashes:
            article.is_duplicate = True
            duplicates.append(article)
            logger.debug(
                "deduplication.batch_duplicate",
                article_id=article.id,
                title=article.title[:50],
            )
            continue

        # Unique article
        seen_hashes.add(article.content_hash)
        unique.append(article)

    logger.info(
        "deduplication.completed",
        unique=len(unique),
        duplicates=len(duplicates),
        total=len(articles),
    )

    return unique, duplicates
