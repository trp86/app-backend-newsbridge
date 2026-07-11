"""Process remaining unprocessed articles."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import setup_logging
from src.core.schemas import Language
from src.editorial import filter_high_quality, process_articles_combined, select_top_stories
from src.storage import ArticleRepository, BriefRepository, TranslationRepository


def main() -> None:
    """Process only unprocessed articles."""
    setup_logging()

    print("=" * 70)
    print("PROCESS REMAINING ARTICLES")
    print("=" * 70)

    # Step 1: Load all articles
    print("\n1. Loading articles from database...")
    all_articles = ArticleRepository.get_recent_articles(limit=97)
    print(f"   ✓ Loaded {len(all_articles)} total articles")

    # Step 2: Get already processed article IDs
    print("\n2. Checking which articles are already processed...")
    existing_briefs = BriefRepository.get_recent_briefs(limit=100)
    processed_article_ids = {brief.article_id for brief in existing_briefs}
    print(f"   ✓ Found {len(processed_article_ids)} already processed")

    # Step 3: Filter out already processed articles
    unprocessed_articles = [
        article for article in all_articles if article.id not in processed_article_ids
    ]
    print(f"   ✓ Found {len(unprocessed_articles)} unprocessed articles")

    if not unprocessed_articles:
        print("\n   🎉 All articles are already processed!")
        return

    # Step 4: Quality filter
    print("\n3. Quality filtering unprocessed articles...")
    high_quality = filter_high_quality(unprocessed_articles, min_score=0.7)
    print(f"   ✓ High quality: {len(high_quality)}")

    if not high_quality:
        print("   ❌ No high-quality unprocessed articles found!")
        return

    # Step 5: Select top stories (limit to 20 to avoid quota issues)
    print("\n4. Selecting top stories...")
    batch_size = min(20, len(high_quality))
    top_stories = select_top_stories(high_quality, count=batch_size)
    print(f"   ✓ Selected {len(top_stories)} stories for processing")

    # Step 6: Process with combined approach
    print(f"\n5. Processing {len(top_stories)} articles...")
    print(f"   📡 Calling Gemini API {len(top_stories)} times...")
    print(f"   (Using gemini-1.5-flash, ~{len(top_stories) * 15} seconds / {len(top_stories) * 15 // 60} minutes)")

    briefs, translations = process_articles_combined(top_stories, target_language=Language.ODIA)

    print(f"\n   ✓ Successfully processed: {len(briefs)} articles")
    print(f"   ✓ Failed: {len(top_stories) - len(briefs)} articles")

    # Step 7: Save to database
    if briefs and translations:
        print("\n6. Saving to database...")

        # Save briefs
        print("   💾 Saving English briefs...")
        briefs_inserted = BriefRepository.insert_briefs(briefs)
        print(f"   ✓ Inserted {briefs_inserted} new briefs")

        # Save translations
        print("   💾 Saving Odia translations...")
        translations_inserted = TranslationRepository.insert_translations(translations)
        print(f"   ✓ Inserted {translations_inserted} new translations")

        # Verify counts
        print("\n7. Verifying database...")
        brief_count = BriefRepository.count_briefs()
        translation_counts = TranslationRepository.count_translations()

        print(f"   ✓ Total briefs in database: {brief_count}")
        print(f"   ✓ Total translations in database: {translation_counts['total']}")

        print("\n" + "=" * 70)
        print("✅ PROCESSING COMPLETE")
        print("=" * 70)

        print(f"\n📊 Summary:")
        print(f"  Total articles in DB: {len(all_articles)}")
        print(f"  Previously processed: {len(processed_article_ids)}")
        print(f"  Newly processed: {len(briefs)}")
        print(f"  Total now processed: {brief_count}")
        print(f"  Remaining unprocessed: {len(all_articles) - brief_count}")

        if brief_count < len(all_articles):
            remaining = len(all_articles) - brief_count
            print(f"\n💡 To process remaining {remaining} articles:")
            print(f"  python -X utf8 scripts/process_remaining_articles.py")

    else:
        print("\n   ❌ No data to save!")


if __name__ == "__main__":
    main()
