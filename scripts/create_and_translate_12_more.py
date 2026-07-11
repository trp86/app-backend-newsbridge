"""Create 12 more briefs and translate them using Google Gemini 1.5 Flash."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import setup_logging
from src.core.schemas import Language
from src.editorial import filter_high_quality, process_articles_combined, select_top_stories
from src.storage import ArticleRepository, BriefRepository, TranslationRepository


def main() -> None:
    """Create 12 more briefs and translate them."""
    setup_logging()

    print("=" * 70)
    print("CREATE + TRANSLATE 12 MORE BRIEFS WITH GEMINI 1.5 FLASH")
    print("=" * 70)

    # Check current state
    existing_briefs = BriefRepository.get_recent_briefs(limit=1000)
    existing_translations = TranslationRepository.get_translations_by_language(
        Language.ODIA, limit=1000
    )
    translated_ids = {t.brief_id for t in existing_translations}

    print(f"\nCurrent state:")
    print(f"  Existing briefs: {len(existing_briefs)}")
    print(f"  Existing translations: {len(existing_translations)}")
    print(f"  Untranslated briefs: {len([b for b in existing_briefs if b.id not in translated_ids])}")

    # Step 1: Load articles
    print("\n1. Loading articles from database...")
    articles = ArticleRepository.get_recent_articles(limit=100)

    if not articles:
        print("   ERROR: No articles found!")
        return

    print(f"   OK: Loaded {len(articles)} articles")

    # Step 2: Quality filter
    print("\n2. Quality filtering...")
    high_quality = filter_high_quality(articles, min_score=0.6)
    print(f"   OK: High quality: {len(high_quality)}")

    if len(high_quality) < 12:
        print(f"   ERROR: Not enough high-quality articles ({len(high_quality)} < 12)")
        print("   Try lowering min_score or fetching more articles")
        return

    # Step 3: Select top stories (12 new ones)
    print("\n3. Selecting 12 new stories...")
    top_stories = select_top_stories(high_quality, count=12)
    print(f"   OK: Selected {len(top_stories)} stories")

    # Step 4: Process with combined approach (Summarize + Translate in ONE call)
    print("\n4. Processing articles with Gemini (Summarize + Translate)...")
    print(f"   --> Calling Gemini API {len(top_stories)} times...")
    print(f"   (Estimated time: {len(top_stories) * 10} seconds)")

    briefs, translations = process_articles_combined(
        top_stories, target_language=Language.ODIA
    )

    print(f"\n   OK: Successfully processed: {len(briefs)} articles")
    print(f"   OK: Created {len(translations)} translations")
    print(f"   Failed: {len(top_stories) - len(briefs)} articles")

    # Step 5: Save to database
    if briefs and translations:
        print("\n5. Saving to database...")

        # Save briefs
        print("   Saving English briefs...")
        briefs_inserted = BriefRepository.insert_briefs(briefs)
        print(f"   OK: Inserted {briefs_inserted} briefs")

        # Save translations
        print("   Saving Odia translations...")
        translations_inserted = TranslationRepository.insert_translations(translations)
        print(f"   OK: Inserted {translations_inserted} translations")

        # Final stats
        print("\n6. Final statistics:")
        brief_count = BriefRepository.count_briefs()
        translation_counts = TranslationRepository.count_translations()

        print(f"   Total briefs in database: {brief_count}")
        print(f"   Total translations: {translation_counts['total']}")
        print(f"   By language: {translation_counts['by_language']}")

        # Show sample
        print("\n7. Sample translation:")
        print("-" * 70)
        if translations:
            sample = translations[0]
            print(f"Brief ID: {sample.brief_id}")
            print(f"Title: {sample.title[:80]}...")
            print(f"30-word: {sample.summary_30[:100]}...")
            print(f"Model: {sample.model_used}")
            print(f"Language: {sample.language.value}")

        print("-" * 70)
        print("\nCOMPLETE: Created and translated {0} new briefs!".format(len(briefs)))
        print(f"   Briefs saved: {briefs_inserted}")
        print(f"   Translations saved: {translations_inserted}")
        print(f"   Model used: gemini-1.5-flash")
        print(f"   API calls made: {len(briefs)} (50% savings vs separate calls)")

    else:
        print("\n   ERROR: No data to save!")


if __name__ == "__main__":
    main()
