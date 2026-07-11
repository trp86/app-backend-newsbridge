"""Test script for combined processing (Summarize + Translate in ONE call)."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import setup_logging
from src.core.schemas import Language
from src.editorial import filter_high_quality, process_articles_combined, select_top_stories
from src.storage import ArticleRepository


def main() -> None:
    """Test combined processing with real articles."""
    setup_logging()

    print("=" * 70)
    print("COMBINED PIPELINE TEST (ONE API CALL)")
    print("Summarization + Translation in ONE call")
    print("=" * 70)

    # Step 1: Load articles
    print("\n1. Loading articles from database...")
    articles = ArticleRepository.get_recent_articles(limit=20)

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
    top_stories = select_top_stories(high_quality, count=3)  # Just 3 for testing
    print(f"   ✓ Selected {len(top_stories)} stories")

    print("\n   Top Stories:")
    for i, article in enumerate(top_stories, 1):
        print(f"\n   [{i}] {article.title[:60]}...")
        print(f"       Source: {article.source_name}")
        print(f"       Content: {len(article.content)} chars")

    # Step 4: Process with combined approach (ONE CALL per article)
    print("\n4. Processing with COMBINED approach (Summarize + Translate)...")
    print(f"   📡 Calling Gemini API {len(top_stories)} times...")
    print("   (This will take 30-45 seconds)")
    print()
    print("   Each call generates:")
    print("   - English: title + 30/111/250 word summaries")
    print("   - Odia: title + 30/111/250 word translations")
    print("   - Total: 8 fields per article in ONE API response")

    briefs, translations = process_articles_combined(top_stories, target_language=Language.ODIA)

    print(f"\n   ✓ Successfully processed: {len(briefs)} articles")
    print(f"   ✓ Failed: {len(top_stories) - len(briefs)} articles")

    # Step 5: Show results
    if briefs and translations:
        print("\n5. Combined Processing Results:")
        print("\n" + "=" * 70)

        for i, (brief, translation) in enumerate(zip(briefs, translations), 1):
            print(f"\n📰 STORY {i}")
            print("-" * 70)
            print(f"Model: {brief.model_used}")
            print(f"API calls: 1 (instead of 2)")

            print(f"\n🇬🇧 ENGLISH (Brief):")
            print(f"Title: {brief.title}")
            print(f"\n30-word:")
            print(f"  {brief.summary_30}")
            print(f"\n111-word:")
            print(f"  {brief.summary_111[:150]}...")
            print(f"\n250-word:")
            print(f"  {brief.summary_250[:200]}...")

            print(f"\n🇮🇳 ODIA (Translation):")
            print(f"Title: {translation.title}")
            print(f"\n30-word:")
            print(f"  {translation.summary_30}")
            print(f"\n111-word:")
            print(f"  {translation.summary_111[:150]}...")
            print(f"\n250-word:")
            print(f"  {translation.summary_250[:200]}...")

        print("\n" + "=" * 70)
        print("✅ COMBINED PIPELINE COMPLETE")
        print("=" * 70)

        print(f"\nSummary:")
        print(f"  Articles processed: {len(top_stories)}")
        print(f"  Successful: {len(briefs)}")
        print(f"  API calls made: {len(briefs)} (50% savings!)")
        print(f"  Model: {briefs[0].model_used if briefs else 'N/A'}")
        print(f"  Languages: English + Odia")
        print()
        print("💡 Traditional approach would use: {} API calls".format(len(briefs) * 2))
        print("💡 Combined approach used: {} API calls".format(len(briefs)))
        print("💡 Savings: {}%".format(50))

    else:
        print("\n   ❌ All processing failed!")


if __name__ == "__main__":
    main()
