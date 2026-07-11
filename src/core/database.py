"""Database connection and initialization (Postgres/SQLite)."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import psycopg
import structlog

from src.core.config import get_settings

logger = structlog.get_logger()


def _use_postgres() -> bool:
    """Check if Postgres should be used based on configuration."""
    settings = get_settings()
    return bool(settings.database_url)


def get_placeholder() -> str:
    """Get the correct SQL placeholder for the current database.

    Returns:
        '%s' for Postgres, '?' for SQLite
    """
    return "%s" if _use_postgres() else "?"


def get_scalar(result: Any, index: int | str = 0) -> Any:
    """Get a scalar value from a database result row.

    Handles both dict (Postgres with dict_row) and tuple/Row (SQLite with Row factory).

    Args:
        result: Result row from cursor.fetchone()
        index: Column index (int for tuple) or name (str for dict)

    Returns:
        The value at the specified index/column

    Example:
        result = cursor.fetchone()
        count = get_scalar(result, "count")  # Works for both Postgres and SQLite
    """
    if isinstance(result, dict):
        # Postgres dict_row
        return result[index] if isinstance(index, str) else list(result.values())[index]
    else:
        # SQLite Row or tuple
        return result[index]


@contextmanager
def get_db_connection() -> Generator[Any, None, None]:
    """Context manager for database connections (Postgres or SQLite).

    Yields:
        Database connection with appropriate configuration

    Example:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM articles")
            rows = cursor.fetchall()
    """
    settings = get_settings()

    if _use_postgres():
        # Neon Postgres connection
        conn = psycopg.connect(settings.database_url)
        conn.row_factory = psycopg.rows.dict_row
    else:
        # SQLite fallback
        conn = sqlite3.connect(settings.database_path)
        conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
        logger.debug("database.commit")
    except Exception as e:
        conn.rollback()
        logger.error("database.rollback", error=str(e))
        raise
    finally:
        conn.close()
        logger.debug("database.close")


def init_database() -> None:
    """Initialize database schema if not exists.

    Creates tables and indexes based on schema.sql.
    Automatically detects Postgres or SQLite and adjusts schema.

    Raises:
        FileNotFoundError: If schema.sql file not found
        DatabaseError: If database initialization fails
    """
    settings = get_settings()

    if not _use_postgres():
        # Create data directory for SQLite
        settings.database_path.parent.mkdir(parents=True, exist_ok=True)

    # Read schema file (relative to project root)
    current_dir = Path(__file__).parent
    schema_path = current_dir.parent.parent / "data" / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    schema_sql = schema_path.read_text(encoding="utf-8")

    # Adjust schema for Postgres
    if _use_postgres():
        schema_sql = _convert_schema_to_postgres(schema_sql)

    # Execute schema
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if _use_postgres():
            # Postgres: execute the entire script at once
            cursor.execute(schema_sql)
        else:
            # SQLite: use executescript for multiple statements
            cursor.executescript(schema_sql)
        logger.info(
            "database.initialized",
            database_type="postgres" if _use_postgres() else "sqlite",
        )


def _convert_schema_to_postgres(schema_sql: str) -> str:
    """Convert SQLite schema to Postgres-compatible schema.

    Args:
        schema_sql: SQLite schema SQL

    Returns:
        Postgres-compatible schema SQL
    """
    # Replace SQLite types and functions with Postgres equivalents
    replacements = {
        "BOOLEAN DEFAULT 0": "BOOLEAN DEFAULT FALSE",
        "BOOLEAN DEFAULT 1": "BOOLEAN DEFAULT TRUE",
        "TIMESTAMP DEFAULT CURRENT_TIMESTAMP": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "INTEGER": "INTEGER",
        "REAL": "NUMERIC",
        "TEXT": "TEXT",
    }

    result = schema_sql
    for old, new in replacements.items():
        result = result.replace(old, new)

    return result


def check_database_health() -> dict[str, int]:
    """Check database health by counting rows in each table.

    Returns:
        Dictionary mapping table names to row counts

    Example:
        health = check_database_health()
        print(f"Articles: {health['articles']}")
    """
    tables = [
        "articles",
        "briefs",
        "translations",
        "publications",
        "publication_stories",
        "api_logs",
    ]

    health = {}

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            result = cursor.fetchone()
            if _use_postgres():
                # Postgres with dict_row returns a dict
                count = result["count"] if isinstance(result, dict) else result[0]
            else:
                # SQLite with Row factory
                count = result[0]
            health[table] = count

    logger.info("database.health_check", **health)
    return health
