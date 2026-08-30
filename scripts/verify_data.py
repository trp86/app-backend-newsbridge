"""
Post-pipeline data verification script.

Queries the database after a pipeline run and checks that:
  - All 11 countries have articles
  - All 11 countries have briefs (native-language sources only)
  - All 13 language translations are populated
  - No country has articles but zero briefs
  - Data was fetched within the last 24 hours

Exits with code 0 on success, 1 if any FAIL check is found.

Usage:
    python scripts/verify_data.py
"""

import os
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path


# ---------------------------------------------------------------------------
# DB connection (standalone — no src imports)
# ---------------------------------------------------------------------------

def _use_postgres() -> bool:
    return bool(os.environ.get("DATABASE_URL", "").strip())


@contextmanager
def _connect():
    if _use_postgres():
        try:
            import psycopg
        except ImportError:
            print("ERROR: psycopg not installed.")
            sys.exit(1)
        conn = psycopg.connect(os.environ["DATABASE_URL"])
        conn.row_factory = psycopg.rows.dict_row
    else:
        db_path = os.environ.get("DATABASE_PATH", "data/brief.db")
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


def _rows(conn, sql: str, params: tuple = ()) -> list:
    cursor = conn.cursor()
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    return [dict(r) if not isinstance(r, dict) else r for r in rows]


def _scalar(conn, sql: str, params: tuple = ()):
    cursor = conn.cursor()
    cursor.execute(sql, params)
    row = cursor.fetchone()
    if row is None:
        return None
    return row[0] if not isinstance(row, dict) else list(row.values())[0]


# ---------------------------------------------------------------------------
# Check helpers
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

EXPECTED_COUNTRIES = {"DE", "JP", "KR", "PL", "BD", "BR", "MX", "QA", "TR", "VN", "CN"}
EXPECTED_LANGUAGES = {"en", "or", "hi", "ta", "kn", "es", "yue", "ms", "nl", "tr", "ar", "bn", "te"}


def _status(ok: bool, critical: bool = True) -> str:
    if ok:
        return PASS
    return FAIL if critical else WARN


def _print_check(label: str, status: str, detail: str = "") -> None:
    icon = "✓" if status == PASS else ("✗" if status == FAIL else "!")
    suffix = f"  — {detail}" if detail else ""
    print(f"  [{icon}] {status:<4}  {label}{suffix}")


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------

def check_articles_exist(conn) -> tuple[str, str]:
    total = _scalar(conn, "SELECT COUNT(*) FROM articles WHERE is_duplicate = FALSE")
    status = _status(total > 0)
    return "Articles exist in DB", status, f"{total} unique articles"


def check_articles_per_country(conn) -> list[tuple]:
    rows = _rows(conn, """
        SELECT country, COUNT(*) AS cnt
        FROM articles
        WHERE is_duplicate = FALSE AND country != ''
        GROUP BY country
    """)
    found = {r["country"] for r in rows}
    missing = EXPECTED_COUNTRIES - found
    results = []
    for r in sorted(rows, key=lambda x: x["country"]):
        results.append((
            f"  Articles: {r['country']}",
            PASS,
            f"{r['cnt']} articles",
        ))
    for country in sorted(missing):
        results.append((
            f"  Articles: {country}",
            FAIL,
            "0 articles — no data ingested",
        ))
    return results


def check_briefs_exist(conn) -> tuple[str, str, str]:
    total = _scalar(conn, "SELECT COUNT(*) FROM briefs")
    status = _status(total > 0)
    return "Briefs exist in DB", status, f"{total} briefs"


def check_briefs_per_country(conn) -> list[tuple]:
    rows = _rows(conn, """
        SELECT country, source_priority, COUNT(*) AS cnt
        FROM briefs
        GROUP BY country, source_priority
        ORDER BY country, source_priority
    """)
    native = {r["country"]: r["cnt"] for r in rows if r["source_priority"] == 1}
    results = []
    for country in sorted(EXPECTED_COUNTRIES):
        cnt = native.get(country, 0)
        results.append((
            f"  Briefs (native): {country}",
            _status(cnt > 0),
            f"{cnt} briefs",
        ))
    return results


def check_translations_per_language(conn) -> list[tuple]:
    rows = _rows(conn, """
        SELECT language, COUNT(*) AS cnt
        FROM translations
        GROUP BY language
    """)
    found = {r["language"]: r["cnt"] for r in rows}
    results = []
    for lang in sorted(EXPECTED_LANGUAGES):
        cnt = found.get(lang, 0)
        results.append((
            f"  Translations: {lang}",
            _status(cnt > 0),
            f"{cnt} translations",
        ))
    return results


def check_pipeline_completeness(conn) -> tuple[str, str, str]:
    """Check no country has articles but zero briefs."""
    rows = _rows(conn, """
        SELECT
            a.country,
            COUNT(DISTINCT a.id) AS articles,
            COUNT(DISTINCT b.id) AS briefs
        FROM articles a
        LEFT JOIN briefs b ON b.article_id = a.id AND b.source_priority = 1
        WHERE a.is_duplicate = FALSE AND a.country != ''
        GROUP BY a.country
        HAVING COUNT(DISTINCT b.id) = 0
    """)
    broken = [r["country"] for r in rows]
    if broken:
        return (
            "Pipeline completeness (articles → briefs)",
            FAIL,
            f"Countries with articles but no briefs: {', '.join(sorted(broken))}",
        )
    return "Pipeline completeness (articles → briefs)", PASS, "All countries have briefs"


def check_data_freshness(conn) -> tuple[str, str, str]:
    """Check that at least some articles were fetched in the last 24 hours."""
    cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    ph = "%s" if _use_postgres() else "?"
    recent = _scalar(
        conn,
        f"SELECT COUNT(*) FROM articles WHERE fetched_at > {ph} AND is_duplicate = FALSE",
        (cutoff,),
    )
    status = _status(recent > 0)
    return "Data freshness (last 24h)", status, f"{recent} articles fetched in last 24 hours"


def check_translation_coverage(conn) -> tuple[str, str, str]:
    """Check that translations cover at least 80% of briefs."""
    brief_count = _scalar(conn, "SELECT COUNT(*) FROM briefs") or 0
    if brief_count == 0:
        return "Translation coverage", WARN, "No briefs to translate"
    translation_count = _scalar(conn, "SELECT COUNT(*) FROM translations") or 0
    expected = brief_count * len(EXPECTED_LANGUAGES)
    pct = int((translation_count / expected) * 100) if expected > 0 else 0
    status = _status(pct >= 80, critical=False) if pct < 100 else PASS
    return (
        "Translation coverage",
        status,
        f"{translation_count}/{expected} ({pct}%)",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    db_type = "PostgreSQL (Neon)" if _use_postgres() else "SQLite"
    print("\n" + "=" * 65)
    print("NEWSBRIDGE — POST-PIPELINE DATA VERIFICATION")
    print(f"  Database : {db_type}")
    print(f"  Time     : {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 65)

    failures = 0

    with _connect() as conn:

        # ── Articles ─────────────────────────────────────────────────────────
        print("\n[ Articles ]")
        label, status, detail = check_articles_exist(conn)
        _print_check(label, status, detail)
        if status == FAIL:
            failures += 1

        for label, status, detail in check_articles_per_country(conn):
            _print_check(label, status, detail)
            if status == FAIL:
                failures += 1

        # ── Briefs ───────────────────────────────────────────────────────────
        print("\n[ Briefs ]")
        label, status, detail = check_briefs_exist(conn)
        _print_check(label, status, detail)
        if status == FAIL:
            failures += 1

        for label, status, detail in check_briefs_per_country(conn):
            _print_check(label, status, detail)
            if status == FAIL:
                failures += 1

        # ── Translations ─────────────────────────────────────────────────────
        print("\n[ Translations ]")
        for label, status, detail in check_translations_per_language(conn):
            _print_check(label, status, detail)
            if status == FAIL:
                failures += 1

        label, status, detail = check_translation_coverage(conn)
        _print_check(label, status, detail)
        if status == FAIL:
            failures += 1

        # ── Pipeline health ───────────────────────────────────────────────────
        print("\n[ Pipeline health ]")
        label, status, detail = check_pipeline_completeness(conn)
        _print_check(label, status, detail)
        if status == FAIL:
            failures += 1

        label, status, detail = check_data_freshness(conn)
        _print_check(label, status, detail)
        if status == FAIL:
            failures += 1

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    if failures == 0:
        print(f"RESULT: ALL CHECKS PASSED")
    else:
        print(f"RESULT: {failures} CHECK(S) FAILED")
    print("=" * 65 + "\n")

    sys.exit(0 if failures == 0 else 1)


if __name__ == "__main__":
    main()
