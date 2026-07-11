"""Test script for editorial pipeline (summarization + selection)."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import setup_logging
from src.editorial import filter_high_quality, select_top_stories, summarize_articles
from src.storage import ArticleRepository


def main() -> None:
    """Test editorial pipeline with real articles from database."""
    setup_logging()

    print("=" * 70)
    print("EDITORIAL PIPELINE TEST")
    print("=" * 70)

    # Step 1: Get articles from database
    print("\n1. Loading articles from database...")
    articles = ArticleRepository.get_recent_articles(limit=20)

    if not articles:
        print("   ❌ No articles found in database!")
        print("   Run: python scripts/test_ingestion.py first")
        return

    print(f"   ✓ Loaded {len(articles)} articles")

    # Step 2: Quality filtering
    print("\n2. Quality filtering (min score: 0.7)...")
    high_quality = filter_high_quality(articles)
    print(f"   ✓ High quality: {len(high_quality)}")
    print(f"   ✓ Filtered out: {len(articles) - len(high_quality)}")

    if not high_quality:
        print("   ❌ No high-quality articles found!")
        return

    # Step 3: Story selection
    print("\n3. Selecting top 5 stories...")
    top_stories = select_top_stories(high_quality, count=5)
    print(f"   ✓ Selected {len(top_stories)} stories")

    print("\n   Top Stories:")
    for i, article in enumerate(top_stories, 1):
        hours_old = (
            article.fetched_at - article.published_at
        ).total_seconds() / 3600
        print(f"\n   [{i}] {article.title[:60]}...")
        print(f"       Source: {article.source_name}")
        print(f"       Age: {hours_old:.1f} hours old")
        print(f"       Content: {len(article.content)} chars")

    # Step 4: Summarization (API call - will use real OpenRouter)
    print("\n4. Summarizing top stories with OpenRouter...")
    print(f"   📡 Calling API for {len(top_stories)} articles...")
    print("   (This will take 30-60 seconds)")

    briefs = summarize_articles(top_stories)

    print(f"\n   ✓ Summarized: {len(briefs)} articles")
    print(f"   ✓ Failed: {len(top_stories) - len(briefs)} articles")

    # Step 5: Show results
    if briefs:
        print("\n5. Summarization Results:")
        print("\n" + "=" * 70)

        for i, brief in enumerate(briefs, 1):
            print(f"\n📰 STORY {i}")
            print("-" * 70)
            print(f"Title: {brief.title}")
            print(f"Model: {brief.model_used}")
            print(f"Quality Score: {brief.quality_score}")

            print(f"\n30-word summary:")
            print(f"  {brief.summary_30}")

            print(f"\n111-word summary:")
            print(f"  {brief.summary_111[:200]}...")

            print(f"\n250-word summary:")
            print(f"  {brief.summary_250[:300]}...")

        print("\n" + "=" * 70)
        print("✅ EDITORIAL PIPELINE COMPLETE")
        print("=" * 70)

        # Summary
        print(f"\nSummary:")
        print(f"  Articles processed: {len(articles)}")
        print(f"  High quality: {len(high_quality)}")
        print(f"  Top stories selected: {len(top_stories)}")
        print(f"  Successfully summarized: {len(briefs)}")
        print(f"\n  Model used: {briefs[0].model_used if briefs else 'N/A'}")
        print(f"  API calls: {len(briefs)} (3 summaries per article)")

    else:
        print("\n   ❌ All summarizations failed!")
        print("   Check:")
        print("     - OpenRouter API key in .env")
        print("     - API rate limits")
        print("     - Network connectivity")


if __name__ == "__main__":
    main()
