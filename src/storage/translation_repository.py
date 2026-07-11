"""Repository for Translation database operations."""

from datetime import datetime

import structlog

from src.core.database import get_db_connection, get_placeholder
from src.core.schemas import Language, Translation

logger = structlog.get_logger()


class TranslationRepository:
    """Repository for translation database operations."""

    @staticmethod
    def insert_translation(translation: Translation) -> None:
        """Insert translation into database.

        Args:
            translation: Translation to insert

        Raises:
            sqlite3.IntegrityError: If translation with same ID already exists
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                INSERT INTO translations (
                    id, brief_id, language, title,
                    summary_30, summary_111, summary_250,
                    model_used, translated_at
                ) VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})
                """,
                (
                    translation.id,
                    translation.brief_id,
                    translation.language.value,
                    translation.title,
                    translation.summary_30,
                    translation.summary_111,
                    translation.summary_250,
                    translation.model_used,
                    translation.translated_at.isoformat(),
                ),
            )

        logger.debug(
            "repository.translation_inserted",
            translation_id=translation.id,
            brief_id=translation.brief_id,
            language=translation.language.value,
        )

    @staticmethod
    def insert_translations(translations: list[Translation]) -> int:
        """Bulk insert translations into database.

        Args:
            translations: List of Translation objects to insert

        Returns:
            Number of translations successfully inserted
        """
        inserted = 0

        for translation in translations:
            try:
                TranslationRepository.insert_translation(translation)
                inserted += 1
            except Exception as e:
                logger.error(
                    "repository.translation_insert_failed",
                    translation_id=translation.id,
                    error=str(e),
                )
                continue

        logger.info("repository.translations_bulk_insert_completed", inserted=inserted)

        return inserted

    @staticmethod
    def get_translation_by_id(translation_id: str) -> Translation | None:
        """Retrieve translation by ID.

        Args:
            translation_id: Translation ID

        Returns:
            Translation if found, None otherwise
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                SELECT id, brief_id, language, title,
                       summary_30, summary_111, summary_250,
                       model_used, translated_at
                FROM translations
                WHERE id = {ph}
                """,
                (translation_id,),
            )
            row = cursor.fetchone()

        if not row:
            return None

        return Translation(
            id=row["id"],
            brief_id=row["brief_id"],
            language=Language(row["language"]),
            title=row["title"],
            summary_30=row["summary_30"],
            summary_111=row["summary_111"],
            summary_250=row["summary_250"],
            model_used=row["model_used"],
            translated_at=(
                row["translated_at"]
                if isinstance(row["translated_at"], datetime)
                else datetime.fromisoformat(row["translated_at"])
            ),
        )

    @staticmethod
    def get_translations_by_brief(brief_id: str) -> list[Translation]:
        """Get all translations for a brief.

        Args:
            brief_id: Brief ID

        Returns:
            List of translations for the brief
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                SELECT id, brief_id, language, title,
                       summary_30, summary_111, summary_250,
                       model_used, translated_at
                FROM translations
                WHERE brief_id = {ph}
                ORDER BY translated_at DESC
                """,
                (brief_id,),
            )
            rows = cursor.fetchall()

        translations = []
        for row in rows:
            translations.append(
                Translation(
                    id=row["id"],
                    brief_id=row["brief_id"],
                    language=Language(row["language"]),
                    title=row["title"],
                    summary_30=row["summary_30"],
                    summary_111=row["summary_111"],
                    summary_250=row["summary_250"],
                    model_used=row["model_used"],
                    translated_at=(
                row["translated_at"]
                if isinstance(row["translated_at"], datetime)
                else datetime.fromisoformat(row["translated_at"])
            ),
                )
            )

        logger.debug(
            "repository.translations_by_brief_fetched",
            brief_id=brief_id,
            count=len(translations),
        )

        return translations

    @staticmethod
    def get_translations_by_briefs(brief_ids: list[str]) -> dict[str, list[Translation]]:
        """Get all translations for multiple briefs in one query.

        Args:
            brief_ids: List of brief IDs

        Returns:
            Dictionary mapping brief_id to list of translations
        """
        if not brief_ids:
            return {}

        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            placeholders = ",".join([ph] * len(brief_ids))
            cursor.execute(
                f"""
                SELECT id, brief_id, language, title,
                       summary_30, summary_111, summary_250,
                       model_used, translated_at
                FROM translations
                WHERE brief_id IN ({placeholders})
                ORDER BY brief_id, translated_at DESC
                """,
                tuple(brief_ids),
            )
            rows = cursor.fetchall()

        # Group translations by brief_id
        translations_by_brief: dict[str, list[Translation]] = {bid: [] for bid in brief_ids}
        for row in rows:
            translation = Translation(
                id=row["id"],
                brief_id=row["brief_id"],
                language=Language(row["language"]),
                title=row["title"],
                summary_30=row["summary_30"],
                summary_111=row["summary_111"],
                summary_250=row["summary_250"],
                model_used=row["model_used"],
                translated_at=(
                    row["translated_at"]
                    if isinstance(row["translated_at"], datetime)
                    else datetime.fromisoformat(row["translated_at"])
                ),
            )
            translations_by_brief[row["brief_id"]].append(translation)

        logger.debug(
            "repository.translations_by_briefs_fetched",
            brief_count=len(brief_ids),
            translation_count=len(rows),
        )

        return translations_by_brief

    @staticmethod
    def get_translations_by_language(language: Language, limit: int = 50) -> list[Translation]:
        """Get translations by language.

        Args:
            language: Target language
            limit: Maximum number of translations to return

        Returns:
            List of translations in the specified language
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            ph = get_placeholder()
            cursor.execute(
                f"""
                SELECT id, brief_id, language, title,
                       summary_30, summary_111, summary_250,
                       model_used, translated_at
                FROM translations
                WHERE language = {ph}
                ORDER BY translated_at DESC
                LIMIT {ph}
                """,
                (language.value, limit),
            )
            rows = cursor.fetchall()

        translations = []
        for row in rows:
            translations.append(
                Translation(
                    id=row["id"],
                    brief_id=row["brief_id"],
                    language=Language(row["language"]),
                    title=row["title"],
                    summary_30=row["summary_30"],
                    summary_111=row["summary_111"],
                    summary_250=row["summary_250"],
                    model_used=row["model_used"],
                    translated_at=(
                row["translated_at"]
                if isinstance(row["translated_at"], datetime)
                else datetime.fromisoformat(row["translated_at"])
            ),
                )
            )

        logger.debug(
            "repository.translations_by_language_fetched",
            language=language.value,
            count=len(translations),
        )

        return translations

    @staticmethod
    def count_translations() -> dict[str, int]:
        """Count translations by language.

        Returns:
            Dictionary with total count and counts by language
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Total count
            cursor.execute("SELECT COUNT(*) FROM translations")
            total = cursor.fetchone()[0]

            # By language
            cursor.execute(
                """
                SELECT language, COUNT(*) as count
                FROM translations
                GROUP BY language
                ORDER BY count DESC
                """
            )
            by_language = {row["language"]: row["count"] for row in cursor.fetchall()}

        counts = {
            "total": total,
            "by_language": by_language,
        }

        logger.info("repository.translation_counts", **counts)

        return counts
