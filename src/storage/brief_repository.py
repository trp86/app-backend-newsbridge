"""Repository for Brief database operations."""

from datetime import datetime

import structlog

from src.core.database import get_db_connection, get_placeholder
from src.core.schemas import Brief

logger = structlog.get_logger()


class BriefRepository:
    """Repository for brief database operations."""

    @staticmethod
    def insert_brief(brief: Brief) -> None:
        """Insert brief into database.

        Args:
            brief: Brief to insert

        Raises:
            sqlite3.IntegrityError: If brief with same ID already exists
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                INSERT INTO briefs (
                    id, article_id, title,
                    summary_30, summary_111, summary_250,
                    category, quality_score, model_used, processed_at
                ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                """,
                (
                    brief.id,
                    brief.article_id,
                    brief.title,
                    brief.summary_30,
                    brief.summary_111,
                    brief.summary_250,
                    brief.category,
                    brief.quality_score,
                    brief.model_used,
                    brief.processed_at.isoformat(),
                ),
            )

        logger.debug(
            "repository.brief_inserted",
            brief_id=brief.id,
            article_id=brief.article_id,
        )

    @staticmethod
    def insert_briefs(briefs: list[Brief]) -> int:
        """Bulk insert briefs into database.

        Args:
            briefs: List of Brief objects to insert

        Returns:
            Number of briefs successfully inserted
        """
        inserted = 0

        for brief in briefs:
            try:
                BriefRepository.insert_brief(brief)
                inserted += 1
            except Exception as e:
                logger.error(
                    "repository.brief_insert_failed",
                    brief_id=brief.id,
                    error=str(e),
                )
                continue

        logger.info("repository.briefs_bulk_insert_completed", inserted=inserted)

        return inserted

    @staticmethod
    def get_brief_by_id(brief_id: str) -> Brief | None:
        """Retrieve brief by ID.

        Args:
            brief_id: Brief ID

        Returns:
            Brief if found, None otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                SELECT id, article_id, title,
                       summary_30, summary_111, summary_250,
                       category, quality_score, model_used, processed_at
                FROM briefs
                WHERE id = {ph}
                """,
                (brief_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        # Handle datetime: Postgres returns datetime objects, SQLite returns strings
        processed_at = (
            row["processed_at"]
            if isinstance(row["processed_at"], datetime)
            else datetime.fromisoformat(row["processed_at"])
        )

        return Brief(
            id=row["id"],
            article_id=row["article_id"],
            title=row["title"],
            summary_30=row["summary_30"],
            summary_111=row["summary_111"],
            summary_250=row["summary_250"],
            category=row["category"],
            quality_score=row["quality_score"],
            model_used=row["model_used"],
            processed_at=processed_at,
        )

    @staticmethod
    def get_recent_briefs(limit: int = 50) -> list[Brief]:
        """Get most recent briefs.

        Args:
            limit: Maximum number of briefs to return

        Returns:
            List of recent briefs, ordered by processed_at DESC
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                SELECT id, article_id, title,
                       summary_30, summary_111, summary_250,
                       category, quality_score, model_used, processed_at
                FROM briefs
                ORDER BY processed_at DESC
                LIMIT {ph}
                """,
                (limit,),
            )
            rows = cursor.fetchall()

        briefs = []
        for row in rows:
            # Handle datetime: Postgres returns datetime objects, SQLite returns strings
            if row["processed_at"] is None:
                continue  # Skip briefs with no processed_at

            processed_at = (
                row["processed_at"]
                if isinstance(row["processed_at"], datetime)
                else datetime.fromisoformat(row["processed_at"])
            )

            briefs.append(
                Brief(
                    id=row["id"],
                    article_id=row["article_id"],
                    title=row["title"],
                    summary_30=row["summary_30"],
                    summary_111=row["summary_111"],
                    summary_250=row["summary_250"],
                    category=row["category"],
                    quality_score=row["quality_score"],
                    model_used=row["model_used"],
                    processed_at=processed_at,
                )
            )

        logger.debug("repository.recent_briefs_fetched", count=len(briefs))

        return briefs

    @staticmethod
    def count_briefs() -> int:
        """Count total briefs.

        Returns:
            Total number of briefs in database
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM briefs")
            count = cursor.fetchone()[0]

        logger.info("repository.brief_count", count=count)

        return count
