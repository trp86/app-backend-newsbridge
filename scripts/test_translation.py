"""Test script for translation pipeline (English → Odia)."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import setup_logging
from src.core.schemas import Brief, Language
from src.editorial import filter_high_quality, select_top_stories, summarize_articles
from src.storage import ArticleRepository
from src.translation import translate_briefs


def main() -> None:
    """Test translation pipeline with real articles."""
    setup_logging()

    print("=" * 70)
    print("TRANSLATION PIPELINE TEST (English → Odia)")
    print("=" * 70)

    # Step 1: Get articles and summarize (reuse editorial pipeline)
    print("\n1. Loading articles and creating English summaries...")
    articles = ArticleRepository.get_recent_articles(limit=10)

    if not articles:
        print("   ❌ No articles found!")
        return

    high_quality = filter_high_quality(articles)
    top_stories = select_top_stories(high_quality, count=2)  # Just 2 for testing

    print(f"   ✓ Selected {len(top_stories)} stories for translation")

    # Summarize
    print("\n2. Generating English summaries...")
    briefs = summarize_articles(top_stories)

    if not briefs:
        print("   ❌ No briefs created!")
        return

    print(f"   ✓ Created {len(briefs)} English briefs")

    # Step 2: Translate to Odia
    print("\n3. Translating to Odia...")
    print(f"   📡 Calling Gemini API for {len(briefs)} briefs...")
    print("   (This will take 20-40 seconds)")

    translations = translate_briefs(briefs, target_language=Language.ODIA)

    print(f"\n   ✓ Translated: {len(translations)} briefs")
    print(f"   ✓ Failed: {len(briefs) - len(translations)} briefs")

    # Step 3: Show results
    if translations:
        print("\n4. Translation Results:")
        print("\n" + "=" * 70)

        for i, (brief, translation) in enumerate(zip(briefs, translations), 1):
            print(f"\n📰 STORY {i}")
            print("-" * 70)

            print(f"\n🇬🇧 ENGLISH:")
            print(f"Title: {brief.title}")
            print(f"30-word: {brief.summary_30}")

            print(f"\n🇮🇳 ODIA:")
            print(f"Title: {translation.title}")
            print(f"30-word: {translation.summary_30}")

            print(f"\n111-word (Odia):")
            print(f"{translation.summary_111[:200]}...")

            print(f"\n250-word (Odia):")
            print(f"{translation.summary_250[:300]}...")

        print("\n" + "=" * 70)
        print("✅ TRANSLATION PIPELINE COMPLETE")
        print("=" * 70)

        print(f"\nSummary:")
        print(f"  Briefs created: {len(briefs)}")
        print(f"  Translations successful: {len(translations)}")
        print(f"  Language: Odia (ଓଡ଼ିଆ)")
        print(f"  Model: {translations[0].model_used if translations else 'N/A'}")

    else:
        print("\n   ❌ All translations failed!")


if __name__ == "__main__":
    main()
