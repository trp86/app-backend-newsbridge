"""Test script for RSS ingestion pipeline."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import init_database
from src.core.logging import setup_logging
from src.ingestion import collect_articles
from src.ingestion.deduplication import mark_duplicates
from src.storage import ArticleRepository


def main() -> None:
    """Test RSS ingestion pipeline."""
    # Setup
    setup_logging()
    print("=" * 60)
    print("RSS INGESTION PIPELINE TEST")
    print("=" * 60)

    # Initialize database
    print("\n1. Initializing database...")
    init_database()
    print("   [OK] Database ready")

    # Collect articles
    print("\n2. Collecting articles from 5 German news sources...")
    print("   Sources: Tagesschau, SZ, Spiegel, DW, Handelsblatt")
    articles = collect_articles()
    print(f"   [OK] Collected {len(articles)} articles")

    # Deduplicate
    print("\n3. Deduplicating articles...")
    unique, duplicates = mark_duplicates(articles)
    print(f"   [OK] Unique: {len(unique)}")
    print(f"   [OK] Duplicates: {len(duplicates)}")

    # Store in database
    print("\n4. Storing unique articles in database...")
    inserted = ArticleRepository.insert_articles(unique)
    print(f"   [OK] Inserted {inserted} articles")

    # Show statistics
    print("\n5. Database statistics:")
    counts = ArticleRepository.count_articles()
    print(f"   Total articles: {counts['total']}")
    print(f"   Unique articles: {counts['unique']}")
    print(f"   Duplicates: {counts['duplicates']}")

    print("\n   By source:")
    for source, count in counts["by_source"].items():
        print(f"     - {source}: {count}")

    # Show sample articles
    print("\n6. Sample articles (latest 5):")
    recent = ArticleRepository.get_recent_articles(limit=5)
    for i, article in enumerate(recent, 1):
        print(f"\n   [{i}] {article.title[:60]}...")
        print(f"       Source: {article.source_name}")
        print(f"       Published: {article.published_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"       URL: {str(article.source_url)[:60]}...")

    print("\n" + "=" * 60)
    print("PIPELINE TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
