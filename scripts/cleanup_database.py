"""Clean up old articles from database."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.logging import setup_logging
from src.storage.cleanup import cleanup_all


def main() -> None:
    """Run database cleanup."""
    setup_logging()

    print("=" * 60)
    print("DATABASE CLEANUP")
    print("=" * 60)

    print("\nCleaning up old data...")
    print("  - Articles older than 7 days")
    print("  - Briefs older than 30 days")

    stats = cleanup_all(
        article_retention_days=7,
        brief_retention_days=30,
    )

    print(f"\n✅ Cleanup complete!")
    print(f"   Articles deleted: {stats['articles_deleted']}")
    print(f"   Briefs deleted: {stats['briefs_deleted']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
