"""Initialize the SQLite database with schema."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import check_database_health, init_database
from src.core.logging import setup_logging


def main() -> None:
    """Initialize database and verify health."""
    setup_logging()

    print("Initializing database...")
    init_database()

    print("\nChecking database health...")
    health = check_database_health()

    print("\nDatabase initialized successfully!")
    print("\nTable counts:")
    for table, count in health.items():
        print(f"  {table}: {count} rows")


if __name__ == "__main__":
    main()
