"""Full NewsBridge pipeline: ingest → dedup → summarise → translate (11 languages) → store.

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --max-articles 30
    python scripts/run_pipeline.py --min-quality 0.6
    python scripts/run_pipeline.py --dry-run
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import get_db_connection, init_database
from src.core.logging import setup_logging
from src.editorial.quality_filter import filter_high_quality
from src.editorial.story_selector import select_top_stories
from src.editorial.summarizer import summarize_articles
from src.ingestion import collect_articles
from src.ingestion.deduplication import mark_duplicates
from src.storage import ArticleRepository, BriefRepository, TranslationRepository
from src.translation.translator import ALL_TARGET_LANGUAGES, translate_briefs_batch


def _get_processed_article_ids() -> set[str]:
    """Return article IDs that already have a brief in the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT article_id FROM briefs")
        rows = cursor.fetchall()
    return {row["article_id"] if isinstance(row, dict) else row[0] for row in rows}


def run_pipeline(
    max_articles: int = 20,
    min_quality: float = 0.7,
    dry_run: bool = False,
) -> dict:
    start_time = time.time()
    stats: dict = {}

    print("\n" + "=" * 70)
    print(f"{'DRY RUN — ' if dry_run else ''}NEWSBRIDGE PIPELINE")
    print(f"  Started    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Max process: {max_articles} articles")
    print(f"  Min quality: {min_quality}")
    print("=" * 70)

    # ── 1. Init database ─────────────────────────────────────────────────────
    print("\n1. Initialising database...")
    init_database()
    print("   ✓ Database ready")

    # ── 2. Ingest RSS feeds ──────────────────────────────────────────────────
    print("\n2. Fetching RSS feeds (25 sources / 11 countries)...")
    articles = collect_articles()
    print(f"   ✓ Fetched {len(articles)} articles")
    stats["fetched"] = len(articles)

    # ── 3. Deduplicate ───────────────────────────────────────────────────────
    print("\n3. Deduplicating...")
    unique, duplicates = mark_duplicates(articles)
    print(f"   ✓ Unique: {len(unique)}   Duplicates skipped: {len(duplicates)}")
    stats["unique"] = len(unique)
    stats["duplicates"] = len(duplicates)

    # ── 4. Store unique articles (always — articles are free, no API cost) ────
    print("\n4. Storing unique articles...")
    inserted = ArticleRepository.insert_articles(unique)
    print(f"   ✓ Inserted {inserted} new articles")
    stats["articles_inserted"] = inserted

    # ── 5. Quality filter ────────────────────────────────────────────────────
    print(f"\n5. Quality filtering (min score ≥ {min_quality})...")
    high_quality = filter_high_quality(unique, min_score=min_quality)
    print(f"   ✓ Passed: {len(high_quality)} / {len(unique)}")
    stats["high_quality"] = len(high_quality)

    # ── 6. Skip already-processed articles ───────────────────────────────────
    print("\n6. Filtering already-processed articles...")
    processed_ids = _get_processed_article_ids()
    unprocessed = [a for a in high_quality if a.id not in processed_ids]
    already_done = len(high_quality) - len(unprocessed)
    print(f"   ✓ Already processed: {already_done}   New to process: {len(unprocessed)}")
    stats["already_processed"] = already_done
    stats["to_process"] = len(unprocessed)

    if not unprocessed:
        elapsed = int(time.time() - start_time)
        print("\n   Nothing new to process. Pipeline complete.")
        _print_summary(stats, elapsed)
        return stats

    # ── 7. Select top stories ────────────────────────────────────────────────
    print(f"\n7. Selecting top {max_articles} stories by quality + recency...")
    top_stories = select_top_stories(unprocessed, count=max_articles)
    print(f"   ✓ Selected {len(top_stories)} stories")
    stats["selected"] = len(top_stories)

    if dry_run:
        print("\n   DRY RUN — stopping before Gemini API calls.")
        print("   Stories that would be processed:")
        for i, a in enumerate(top_stories, 1):
            print(f"   [{i:2d}] {a.source_name:<30} {a.title[:50]}")
        elapsed = int(time.time() - start_time)
        _print_summary(stats, elapsed)
        return stats

    # ── 8. Summarise (EN briefs) ──────────────────────────────────────────────
    print(f"\n8. Summarising {len(top_stories)} articles → English briefs...")
    print(f"   (1 Gemini call per article, ~{len(top_stories) * 8}s estimated)")
    briefs = summarize_articles(top_stories)
    print(f"   ✓ Briefs created: {len(briefs)} / {len(top_stories)}")
    stats["briefs_created"] = len(briefs)

    if not briefs:
        print("   No briefs created — aborting.")
        elapsed = int(time.time() - start_time)
        _print_summary(stats, elapsed)
        return stats

    # ── 9. Store briefs ───────────────────────────────────────────────────────
    print("\n9. Storing English briefs...")
    briefs_inserted = BriefRepository.insert_briefs(briefs)
    print(f"   ✓ Inserted {briefs_inserted} briefs")
    stats["briefs_inserted"] = briefs_inserted

    # ── 10. Translate to all 11 languages ────────────────────────────────────
    lang_names = ", ".join(l.value for l in ALL_TARGET_LANGUAGES)
    print(f"\n10. Translating to {len(ALL_TARGET_LANGUAGES)} languages ({lang_names})...")
    print(f"    (1 Gemini call per article, ~{len(briefs) * 10}s estimated)")
    translations_by_brief = translate_briefs_batch(briefs, ALL_TARGET_LANGUAGES)
    all_translations = [
        t
        for lang_map in translations_by_brief.values()
        for t in lang_map.values()
    ]
    expected = len(briefs) * len(ALL_TARGET_LANGUAGES)
    print(f"    ✓ Translations created: {len(all_translations)} / {expected}")
    stats["translations_created"] = len(all_translations)

    # ── 11. Store translations ────────────────────────────────────────────────
    print("\n11. Storing translations...")
    translations_inserted = TranslationRepository.insert_translations(all_translations)
    print(f"    ✓ Inserted {translations_inserted} translations")
    stats["translations_inserted"] = translations_inserted

    elapsed = int(time.time() - start_time)
    _print_summary(stats, elapsed)
    return stats


def _print_summary(stats: dict, elapsed: int) -> None:
    gemini_calls = stats.get("briefs_created", 0) * 2
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print(f"  Elapsed          : {elapsed}s")
    print(f"  RSS articles     : {stats.get('fetched', 0)} fetched  →  {stats.get('unique', 0)} unique  →  {stats.get('high_quality', 0)} high-quality")
    print(f"  Already in DB    : {stats.get('already_processed', 0)}")
    print(f"  New briefs       : {stats.get('briefs_created', 0)}")
    print(f"  New translations : {stats.get('translations_created', 0)}  ({len(ALL_TARGET_LANGUAGES)} languages × {stats.get('briefs_created', 0)} briefs)")
    print(f"  Gemini API calls : {gemini_calls}  (summarise + translate per article)")
    print("=" * 70 + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="NewsBridge end-to-end pipeline")
    parser.add_argument(
        "--max-articles",
        type=int,
        default=int(__import__("os").environ.get("MAX_ARTICLES", "20")),
        help="Max articles to summarise/translate per run (default: 20)",
    )
    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.7,
        help="Minimum quality score (default: 0.7)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ingest and dedup only — no Gemini calls, no brief/translation writes",
    )
    args = parser.parse_args()

    setup_logging()

    try:
        run_pipeline(
            max_articles=args.max_articles,
            min_quality=args.min_quality,
            dry_run=args.dry_run,
        )
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
