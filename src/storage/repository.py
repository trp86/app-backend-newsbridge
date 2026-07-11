"""Database repository for CRUD operations."""

from datetime import datetime

import structlog

from src.core.database import get_db_connection, get_placeholder, get_scalar
from src.core.schemas import RawArticle

logger = structlog.get_logger()


class ArticleRepository:
    """Repository for article database operations."""

    @staticmethod
    def insert_article(article: RawArticle) -> None:
        """Insert article into database.

        Args:
            article: RawArticle to insert

        Raises:
            IntegrityError: If article with same ID already exists
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                INSERT INTO articles (
                    id, source_url, source_name, source_type,
                    title, content, published_at, fetched_at,
                    content_hash, is_duplicate
                ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                """,
                (
                    article.id,
                    str(article.source_url),
                    article.source_name,
                    article.source_type.value,
                    article.title,
                    article.content,
                    article.published_at.isoformat(),
                    article.fetched_at.isoformat(),
                    article.content_hash,
                    article.is_duplicate,
                ),
            )

        logger.debug(
            "repository.article_inserted",
            article_id=article.id,
            source=article.source_name,
        )

    @staticmethod
    def insert_articles(articles: list[RawArticle]) -> int:
        """Bulk insert articles into database.

        Args:
            articles: List of RawArticle objects to insert

        Returns:
            Number of articles successfully inserted

        Example:
            count = ArticleRepository.insert_articles(unique_articles)
            logger.info(f"Inserted {count} articles")
        """
        inserted = 0

        for article in articles:
            try:
                ArticleRepository.insert_article(article)
                inserted += 1
            except Exception as e:
                logger.error(
                    "repository.insert_failed",
                    article_id=article.id,
                    error=str(e),
                )
                continue

        logger.info("repository.bulk_insert_completed", inserted=inserted)

        return inserted

    @staticmethod
    def get_article_by_id(article_id: str) -> RawArticle | None:
        """Retrieve article by ID.

        Args:
            article_id: Article ID

        Returns:
            RawArticle if found, None otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                SELECT id, source_url, source_name, source_type,
                       title, content, published_at, fetched_at,
                       content_hash, is_duplicate
                FROM articles
                WHERE id = {ph}
                """,
                (article_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        # Handle datetime: Postgres returns datetime objects, SQLite returns strings
        published_at = row["published_at"] if isinstance(row["published_at"], datetime) else datetime.fromisoformat(row["published_at"])
        fetched_at = row["fetched_at"] if isinstance(row["fetched_at"], datetime) else datetime.fromisoformat(row["fetched_at"])

        return RawArticle(
            id=row["id"],
            source_url=row["source_url"],
            source_name=row["source_name"],
            source_type=row["source_type"],
            title=row["title"],
            content=row["content"],
            published_at=published_at,
            fetched_at=fetched_at,
            content_hash=row["content_hash"],
            is_duplicate=bool(row["is_duplicate"]),
        )

    @staticmethod
    def get_recent_articles(limit: int = 100) -> list[RawArticle]:
        """Get most recent articles.

        Args:
            limit: Maximum number of articles to return

        Returns:
            List of recent articles, ordered by published_at DESC
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                SELECT id, source_url, source_name, source_type,
                       title, content, published_at, fetched_at,
                       content_hash, is_duplicate
                FROM articles
                WHERE is_duplicate = FALSE
                ORDER BY published_at DESC
                LIMIT {ph}
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        articles = []
        for row in rows:
            # Handle datetime: Postgres returns datetime objects, SQLite returns strings
            published_at = row["published_at"] if isinstance(row["published_at"], datetime) else datetime.fromisoformat(row["published_at"])
            fetched_at = row["fetched_at"] if isinstance(row["fetched_at"], datetime) else datetime.fromisoformat(row["fetched_at"])

            articles.append(
                RawArticle(
                    id=row["id"],
                    source_url=row["source_url"],
                    source_name=row["source_name"],
                    source_type=row["source_type"],
                    title=row["title"],
                    content=row["content"],
                    published_at=published_at,
                    fetched_at=fetched_at,
                    content_hash=row["content_hash"],
                    is_duplicate=bool(row["is_duplicate"]),
                )
            )

        logger.debug("repository.recent_articles_fetched", count=len(articles))

        return articles

    @staticmethod
    def count_articles() -> dict[str, int]:
        """Count articles by source.

        Returns:
            Dictionary mapping source names to article counts
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) as count FROM articles")
            total = get_scalar(cursor.fetchone(), "count")

            # Unique (non-duplicate) count
            cursor.execute("SELECT COUNT(*) as count FROM articles WHERE is_duplicate = FALSE")
            unique = get_scalar(cursor.fetchone(), "count")

            # By source
            cursor.execute(
                """
                SELECT source_name, COUNT(*) as count
                FROM articles
                WHERE is_duplicate = FALSE
                GROUP BY source_name
                ORDER BY count DESC
                """
            )
            by_source = {row["source_name"]: row["count"] for row in cursor.fetchall()}

        counts = {
            "total": total,
            "unique": unique,
            "duplicates": total - unique,
            "by_source": by_source,
        }

        logger.info("repository.article_counts", **counts)

        return counts
