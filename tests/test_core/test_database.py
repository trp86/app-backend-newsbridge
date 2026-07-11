"""Tests for database operations."""

import sqlite3
from pathlib import Path

import pytest

from src.core.database import check_database_health, get_db_connection, init_database


def test_init_database(test_env, temp_database):
    """Test database initialization creates schema."""
    init_database()

    assert temp_database.exists()

    # Check tables exist
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "api_logs",
            "articles",
            "briefs",
            "publication_stories",
            "publications",
            "translations",
        ]

        for table in expected_tables:
            assert table in tables


def test_get_db_connection_context_manager(test_env, temp_database):
    """Test database connection context manager."""
    init_database()

    with get_db_connection() as conn:
        assert isinstance(conn, sqlite3.Connection)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()[0]
        assert result == 1


def test_get_db_connection_rollback_on_error(test_env, temp_database):
    """Test database rolls back on error."""
    init_database()

    with pytest.raises(sqlite3.OperationalError):
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO articles VALUES (1, 2, 3)")  # Invalid


def test_check_database_health(test_env, temp_database):
    """Test database health check returns counts."""
    init_database()

    health = check_database_health()

    assert isinstance(health, dict)
    assert "articles" in health
    assert "briefs" in health
    assert "translations" in health
    assert "publications" in health
    assert "publication_stories" in health
    assert "api_logs" in health

    # All tables should be empty initially
    for table, count in health.items():
        assert count == 0


def test_database_indexes_created(test_env, temp_database):
    """Test that indexes are created."""
    init_database()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        )
        indexes = [row[0] for row in cursor.fetchall()]

        assert len(indexes) > 0
        assert "idx_articles_published" in indexes
        assert "idx_articles_hash" in indexes
