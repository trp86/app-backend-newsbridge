"""Database cleanup utilities."""

from datetime import datetime, timedelta

import structlog

from src.core.database import get_db_connection

logger = structlog.get_logger()


def cleanup_old_articles(retention_days: int = 7) -> int:
    """Delete articles older than retention period.

    Args:
        retention_days: Number of days to keep articles (default: 7)

    Returns:
        Number of articles deleted

    Example:
        deleted = cleanup_old_articles(retention_days=7)
        logger.info(f"Cleaned up {deleted} old articles")
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Count articles to delete
        cursor.execute(
            "SELECT COUNT(*) FROM articles WHERE fetched_at < ?",
            (cutoff_date.isoformat(),),
        )
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info("cleanup.no_old_articles", retention_days=retention_days)
            return 0

        # Delete old articles
        cursor.execute(
            "DELETE FROM articles WHERE fetched_at < ?",
            (cutoff_date.isoformat(),),
        )

        logger.info(
            "cleanup.articles_deleted",
            deleted=count,
            retention_days=retention_days,
            cutoff_date=cutoff_date.isoformat(),
        )

        return count


def cleanup_old_briefs(retention_days: int = 30) -> int:
    """Delete briefs older than retention period.

    Args:
        retention_days: Number of days to keep briefs (default: 30)

    Returns:
        Number of briefs deleted
    """
    cutoff_date = datetime.now() - timedelta(days=retention_days)

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Count briefs to delete
        cursor.execute(
            "SELECT COUNT(*) FROM briefs WHERE processed_at < ?",
            (cutoff_date.isoformat(),),
        )
        count = cursor.fetchone()[0]

        if count == 0:
            logger.info("cleanup.no_old_briefs", retention_days=retention_days)
            return 0

        # Delete old briefs (cascades to translations)
        cursor.execute(
            "DELETE FROM briefs WHERE processed_at < ?",
            (cutoff_date.isoformat(),),
        )

        logger.info(
            "cleanup.briefs_deleted",
            deleted=count,
            retention_days=retention_days,
            cutoff_date=cutoff_date.isoformat(),
        )

        return count


def cleanup_all(article_retention_days: int = 7, brief_retention_days: int = 30) -> dict[str, int]:
    """Run all cleanup operations.

    Args:
        article_retention_days: Days to keep raw articles (default: 7)
        brief_retention_days: Days to keep processed briefs (default: 30)

    Returns:
        Dictionary with cleanup statistics

    Example:
        stats = cleanup_all()
        print(f"Deleted {stats['articles']} articles, {stats['briefs']} briefs")
    """
    logger.info("cleanup.started")

    articles_deleted = cleanup_old_articles(article_retention_days)
    briefs_deleted = cleanup_old_briefs(brief_retention_days)

    stats = {
        "articles_deleted": articles_deleted,
        "briefs_deleted": briefs_deleted,
    }

    logger.info("cleanup.completed", **stats)

    return stats
