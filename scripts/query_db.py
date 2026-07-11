"""Query the SQLite database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage import ArticleRepository


def main() -> None:
    """Query and display database contents."""
    print("=" * 60)
    print("DATABASE QUERY")
    print("=" * 60)

    # Get counts
    print("\n📊 Article Counts:")
    counts = ArticleRepository.count_articles()
    print(f"   Total: {counts['total']}")
    print(f"   Unique: {counts['unique']}")
    print(f"   Duplicates: {counts['duplicates']}")

    print("\n   By Source:")
    for source, count in counts["by_source"].items():
        print(f"     • {source}: {count}")

    # Get recent articles
    print("\n📰 Recent Articles (Latest 10):")
    recent = ArticleRepository.get_recent_articles(limit=10)

    for i, article in enumerate(recent, 1):
        print(f"\n   [{i}] {article.title[:80]}")
        print(f"       Source: {article.source_name}")
        print(f"       Published: {article.published_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"       URL: {str(article.source_url)[:70]}...")
        print(f"       Content preview: {article.content[:100]}...")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
