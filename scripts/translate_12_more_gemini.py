"""Translate 12 more briefs using Google Gemini 1.5 Flash."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import setup_logging
from src.core.schemas import Language
from src.storage.brief_repository import BriefRepository
from src.storage.translation_repository import TranslationRepository
from src.translation.translator import translate_brief


def main() -> None:
    """Translate 12 untranslated briefs using Gemini."""
    setup_logging()

    print("=" * 70)
    print("TRANSLATE 12 MORE BRIEFS WITH GOOGLE GEMINI 1.5 FLASH")
    print("=" * 70)

    # Get already translated brief IDs (get Odia translations)
    all_translations = TranslationRepository.get_translations_by_language(
        Language.ODIA, limit=1000
    )
    translated_ids = {t.brief_id for t in all_translations}
    print(f"\nOK Already translated: {len(translated_ids)} briefs")

    # Get all briefs
    all_briefs = BriefRepository.get_recent_briefs(limit=100)
    print(f"OK Total briefs available: {len(all_briefs)}")

    # Filter untranslated
    untranslated = [b for b in all_briefs if b.id not in translated_ids]
    print(f"OK Untranslated briefs: {len(untranslated)}")

    if not untranslated:
        print("\nERROR No untranslated briefs found!")
        return

    # Take first 12
    to_translate = untranslated[:12]
    print(f"\n--> Will translate: {len(to_translate)} briefs to Odia")
    print(f"   (This will take approximately {len(to_translate) * 5} seconds)")

    # Translate each brief
    translations = []
    for i, brief in enumerate(to_translate, 1):
        print(f"\n[{i}/{len(to_translate)}] Translating: {brief.title[:60]}...")
        try:
            translation = translate_brief(brief, target_language=Language.ODIA)
            translations.append(translation)
            print(f"   OK Success: {translation.title[:60]}...")
        except Exception as e:
            print(f"   ERROR Failed: {e}")
            continue

    # Save translations
    if translations:
        print(f"\nSaving Saving {len(translations)} translations to database...")
        inserted = TranslationRepository.insert_translations(translations)
        print(f"   OK Inserted {inserted} translations")

        # Verify
        print("\nStats Final counts:")
        counts = TranslationRepository.count_translations()
        print(f"   Total translations in database: {counts['total']}")
        print(f"   By language: {counts['by_language']}")

        # Show sample
        print("\nSample Sample translation:")
        print("-" * 70)
        sample = translations[0]
        print(f"Brief ID: {sample.brief_id}")
        print(f"Title: {sample.title}")
        print(f"30-word: {sample.summary_30[:100]}...")
        print(f"Model: gemini-1.5-flash")
        print("-" * 70)

        print(f"\nCOMPLETE COMPLETE: Translated {len(translations)}/{len(to_translate)} briefs")
    else:
        print("\nERROR No translations created!")


if __name__ == "__main__":
    main()
