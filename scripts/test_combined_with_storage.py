"""Test script for combined processing WITH database storage."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import setup_logging
from src.core.schemas import Language
from src.editorial import filter_high_quality, process_articles_combined, select_top_stories
from src.storage import ArticleRepository, BriefRepository, TranslationRepository


def main() -> None:
    """Test combined processing and save to database."""
    setup_logging()

    print("=" * 70)
    print("COMBINED PIPELINE + DATABASE STORAGE TEST")
    print("=" * 70)

    # Step 1: Load articles
    print("\n1. Loading articles from database...")
    articles = ArticleRepository.get_recent_articles(limit=50)

    if not articles:
        print("   ❌ No articles found!")
        return

    print(f"   ✓ Loaded {len(articles)} articles")

    # Step 2: Quality filter
    print("\n2. Quality filtering...")
    high_quality = filter_high_quality(articles, min_score=0.7)
    print(f"   ✓ High quality: {len(high_quality)}")

    # Step 3: Select top stories
    print("\n3. Selecting top stories...")
    top_stories = select_top_stories(high_quality, count=20)
    print(f"   ✓ Selected {len(top_stories)} stories")

    # Step 4: Process with combined approach
    print("\n4. Processing articles (Summarize + Translate in ONE call)...")
    print(f"   📡 Calling Gemini API {len(top_stories)} times...")
    print(f"   (This will take approximately {len(top_stories) * 15} seconds / {len(top_stories) * 15 // 60} minutes)")

    briefs, translations = process_articles_combined(top_stories, target_language=Language.ODIA)

    print(f"\n   ✓ Successfully processed: {len(briefs)} articles")
    print(f"   ✓ Failed: {len(top_stories) - len(briefs)} articles")

    # Step 5: Save to database
    if briefs and translations:
        print("\n5. Saving to database...")

        # Save briefs
        print("   💾 Saving English briefs...")
        briefs_inserted = BriefRepository.insert_briefs(briefs)
        print(f"   ✓ Inserted {briefs_inserted} briefs into 'briefs' table")

        # Save translations
        print("   💾 Saving Odia translations...")
        translations_inserted = TranslationRepository.insert_translations(translations)
        print(f"   ✓ Inserted {translations_inserted} translations into 'translations' table")

        # Verify counts
        print("\n6. Verifying database...")
        brief_count = BriefRepository.count_briefs()
        translation_counts = TranslationRepository.count_translations()

        print(f"   ✓ Total briefs in database: {brief_count}")
        print(f"   ✓ Total translations in database: {translation_counts['total']}")
        print(f"   ✓ Translations by language: {translation_counts['by_language']}")

        # Show sample
        print("\n7. Sample from database:")
        print("\n" + "=" * 70)

        # Get first brief
        recent_briefs = BriefRepository.get_recent_briefs(limit=1)
        if recent_briefs:
            brief = recent_briefs[0]
            print(f"\n📰 LATEST BRIEF")
            print("-" * 70)
            print(f"ID: {brief.id}")
            print(f"Title: {brief.title}")
            print(f"30-word: {brief.summary_30[:100]}...")
            print(f"Model: {brief.model_used}")
            print(f"Processed: {brief.processed_at}")

        # Get corresponding translation
        odia_translations = TranslationRepository.get_translations_by_language(
            Language.ODIA, limit=1
        )
        if odia_translations:
            translation = odia_translations[0]
            print(f"\n🇮🇳 LATEST ODIA TRANSLATION")
            print("-" * 70)
            print(f"ID: {translation.id}")
            print(f"Brief ID: {translation.brief_id}")
            print(f"Title: {translation.title}")
            print(f"30-word: {translation.summary_30[:100]}...")
            print(f"Language: {translation.language.value}")
            print(f"Translated: {translation.translated_at}")

        print("\n" + "=" * 70)
        print("✅ COMPLETE: PROCESSING + STORAGE SUCCESS")
        print("=" * 70)

        print(f"\n📊 Summary:")
        print(f"  Articles processed: {len(top_stories)}")
        print(f"  Briefs created: {len(briefs)}")
        print(f"  Translations created: {len(translations)}")
        print(f"  Briefs saved to DB: {briefs_inserted}")
        print(f"  Translations saved to DB: {translations_inserted}")
        print(f"  API calls: {len(briefs)} (50% savings)")

        print(f"\n💡 Query your data:")
        print(f"  sqlite3 data/brief.db \"SELECT * FROM briefs LIMIT 3;\"")
        print(f"  sqlite3 data/brief.db \"SELECT * FROM translations WHERE language='or' LIMIT 3;\"")

    else:
        print("\n   ❌ No data to save!")


if __name__ == "__main__":
    main()
