"""
Standalone 7-day retention cleanup script.

Deletes articles (and all related data) older than RETENTION_DAYS from the database.
Supports both Neon PostgreSQL (DATABASE_URL) and SQLite (DATABASE_PATH).

Usage:
    python scripts/retention_cleanup.py
    python scripts/retention_cleanup.py --days 14
    python scripts/retention_cleanup.py --dry-run
"""

import argparse
import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# Database connection (no src imports — fully standalone)
# ---------------------------------------------------------------------------

def _use_postgres() -> bool:
    return bool(os.environ.get("DATABASE_URL", "").strip())


@contextmanager
def _connect():
    if _use_postgres():
        try:
            import psycopg
        except ImportError:
            print("ERROR: psycopg not installed. Run: pip install psycopg[binary]")
            sys.exit(1)
        conn = psycopg.connect(os.environ["DATABASE_URL"])
        conn.row_factory = psycopg.rows.dict_row
    else:
        db_path = os.environ.get("DATABASE_PATH", "data/brief.db")
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _ph() -> str:
    """SQL placeholder: %s for Postgres, ? for SQLite."""
    return "%s" if _use_postgres() else "?"


# ---------------------------------------------------------------------------
# Cleanup logic
# ---------------------------------------------------------------------------

def count_rows(conn, table: str, where_clause: str, params: tuple) -> int:
    ph = _ph()
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {where_clause}", params)
    row = cursor.fetchone()
    return row["count"] if isinstance(row, dict) else row[0]


def delete_rows(conn, table: str, where_clause: str, params: tuple) -> int:
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE {where_clause}", params)
    return cursor.rowcount


def run_cleanup(retention_days: int = 7, dry_run: bool = False) -> dict[str, int]:
    cutoff = datetime.now() - timedelta(days=retention_days)
    ph = _ph()

    print(f"\n{'DRY RUN — ' if dry_run else ''}Retention cleanup")
    print(f"  Database : {'PostgreSQL (Neon)' if _use_postgres() else 'SQLite'}")
    print(f"  Cutoff   : articles published before {cutoff.strftime('%Y-%m-%d %H:%M')} UTC")
    print(f"  Retain   : last {retention_days} days\n")

    stats: dict[str, int] = {}

    with _connect() as conn:
        # ------------------------------------------------------------------
        # Count what will be deleted
        # ------------------------------------------------------------------
        old_articles_subquery = (
            f"SELECT id FROM articles WHERE published_at < {ph}"
        )
        old_briefs_subquery = (
            f"SELECT id FROM briefs WHERE article_id IN ({old_articles_subquery})"
        )
        old_translations_subquery = (
            f"SELECT id FROM translations WHERE brief_id IN ({old_briefs_subquery})"
        )

        counts = {
            "publication_stories": count_rows(
                conn,
                "publication_stories",
                f"translation_id IN ({old_translations_subquery})",
                (cutoff,),
            ),
            "publications": count_rows(
                conn,
                "publications",
                f"date < {ph}",
                (cutoff.date(),),
            ),
            "translations": count_rows(
                conn,
                "translations",
                f"brief_id IN ({old_briefs_subquery})",
                (cutoff,),
            ),
            "briefs": count_rows(
                conn,
                "briefs",
                f"article_id IN ({old_articles_subquery})",
                (cutoff,),
            ),
            "articles": count_rows(
                conn,
                "articles",
                f"published_at < {ph}",
                (cutoff,),
            ),
        }

        total = sum(counts.values())
        print("  Rows to delete:")
        for table, n in counts.items():
            marker = "  (nothing)" if n == 0 else ""
            print(f"    {table:<25} {n:>6}{marker}")
        print(f"    {'TOTAL':<25} {total:>6}\n")

        if dry_run:
            print("  Dry run — no rows deleted.")
            return counts

        if total == 0:
            print("  Nothing to delete. Database is already clean.")
            return counts

        # ------------------------------------------------------------------
        # Delete in foreign-key order
        # ------------------------------------------------------------------
        stats["publication_stories"] = delete_rows(
            conn,
            "publication_stories",
            f"translation_id IN ({old_translations_subquery})",
            (cutoff,),
        )
        stats["publications"] = delete_rows(
            conn,
            "publications",
            f"date < {ph}",
            (cutoff.date(),),
        )
        stats["translations"] = delete_rows(
            conn,
            "translations",
            f"brief_id IN ({old_briefs_subquery})",
            (cutoff,),
        )
        stats["briefs"] = delete_rows(
            conn,
            "briefs",
            f"article_id IN ({old_articles_subquery})",
            (cutoff,),
        )
        stats["articles"] = delete_rows(
            conn,
            "articles",
            f"published_at < {ph}",
            (cutoff,),
        )

    print("  Deleted:")
    for table, n in stats.items():
        print(f"    {table:<25} {n:>6}")
    print(f"\n  Cleanup complete at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")

    return stats


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="7-day retention cleanup for NewsBridge DB")
    parser.add_argument(
        "--days",
        type=int,
        default=int(os.environ.get("RETENTION_DAYS", "7")),
        help="Number of days to retain (default: 7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without deleting anything",
    )
    args = parser.parse_args()

    try:
        run_cleanup(retention_days=args.days, dry_run=args.dry_run)
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
