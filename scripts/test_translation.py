"""
Quick local test for the batch translation fix (max_output_tokens increase).

Fetches 1 brief from the DB that has no translations yet,
runs the full batch translation (all 11 languages in one Gemini call),
prints the result, and optionally stores it.

Usage:
    python scripts/test_translation.py              # translate 1 brief, print only
    python scripts/test_translation.py --store      # translate 1 brief and store in DB
    python scripts/test_translation.py --count 3    # translate 3 briefs
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import get_db_connection, get_placeholder, init_database
from src.core.logging import setup_logging
from src.core.schemas import Language
from src.storage.brief_repository import BriefRepository
from src.storage.translation_repository import TranslationRepository
from src.translation.translator import ALL_TARGET_LANGUAGES, translate_brief_batch


def get_untranslated_brief_ids(limit: int) -> list[str]:
    ph = get_placeholder()
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT b.id FROM briefs b
            WHERE NOT EXISTS (
                SELECT 1 FROM translations t WHERE t.brief_id = b.id
            )
            LIMIT {ph}
            """,
            (limit,),
        )
        rows = cursor.fetchall()
    return [r["id"] if isinstance(r, dict) else r[0] for r in rows]


def main():
    parser = argparse.ArgumentParser(description="Test batch translation locally")
    parser.add_argument("--count", type=int, default=1, help="Number of briefs to translate (default: 1)")
    parser.add_argument("--store", action="store_true", help="Store translations in DB after success")
    args = parser.parse_args()

    setup_logging()
    init_database()

    print("\n" + "=" * 65)
    print("BATCH TRANSLATION TEST")
    print(f"  Languages : {len(ALL_TARGET_LANGUAGES)} ({', '.join(l.value for l in ALL_TARGET_LANGUAGES)})")
    print(f"  Store     : {args.store}")
    print("=" * 65)

    # ── Fetch untranslated briefs ────────────────────────────────────────────
    print(f"\nFetching {args.count} untranslated brief(s) from DB...")
    ids = get_untranslated_brief_ids(args.count)

    if not ids:
        print("No untranslated briefs found.")
        print("Hint: run the pipeline first → python scripts/run_pipeline.py --max-articles 5")
        sys.exit(0)

    briefs = [BriefRepository.get_brief_by_id(bid) for bid in ids]
    briefs = [b for b in briefs if b is not None]
    print(f"Found {len(briefs)} brief(s)\n")

    # ── Translate each brief ─────────────────────────────────────────────────
    all_translations = []
    failed = 0

    total_stored = 0

    for i, brief in enumerate(briefs, 1):
        print(f"[{i}/{len(briefs)}] Brief  : {brief.title[:60]}")
        print(f"         Country: {brief.country}  |  Priority: {brief.source_priority}")

        try:
            result = translate_brief_batch(brief, ALL_TARGET_LANGUAGES)
            translations = list(result.values())
            all_translations.extend(translations)
            print(f"         OK {len(translations)}/{len(ALL_TARGET_LANGUAGES)} languages translated")

            # Print a sample in 3 languages
            for lang_code in ("en", "hi", "ar"):
                lang = Language(lang_code)
                if lang in result:
                    t = result[lang]
                    print(f"    [{lang_code}] {t.title}")
                    print(f"         {t.summary_30}")

            # Store immediately so progress is not lost on subsequent failures
            if args.store:
                inserted = TranslationRepository.insert_translations(translations)
                total_stored += inserted
                print(f"         Stored {inserted} translations in DB\n")
            else:
                print()

        except Exception as e:
            failed += 1
            print(f"         FAILED: {e}\n")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("=" * 65)
    print(f"Result : {len(all_translations)} translations created, {failed} brief(s) failed")
    if args.store:
        print(f"Stored : {total_stored} rows written to DB")
        print("\nVerify with:")
        print("  SELECT language, COUNT(*) FROM translations GROUP BY language;")
    else:
        print("\nRun with --store to write to DB:")
        print("  python scripts/test_translation.py --store")

    print("=" * 65 + "\n")
    sys.exit(1 if failed == len(briefs) else 0)


if __name__ == "__main__":
    main()
