"""Tests for article repository."""

from datetime import datetime

import pytest

from src.core.database import init_database
from src.core.schemas import RawArticle, SourceType
from src.storage.repository import ArticleRepository


@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return RawArticle(
        id="test123",
        source_url="https://example.com/article",
        source_name="Test Source",
        source_type=SourceType.RSS,
        title="Test Article",
        content="Test content here",
        published_at=datetime(2026, 7, 4, 12, 0, 0),
        fetched_at=datetime(2026, 7, 4, 13, 0, 0),
        content_hash="abc123hash",
        is_duplicate=False,
    )


def test_insert_article(test_env, temp_database, sample_article):
    """Test inserting a single article."""
    init_database()

    ArticleRepository.insert_article(sample_article)

    # Verify insertion
    retrieved = ArticleRepository.get_article_by_id("test123")
    assert retrieved is not None
    assert retrieved.title == "Test Article"
    assert retrieved.source_name == "Test Source"


def test_insert_article_duplicate_id(test_env, temp_database, sample_article):
    """Test inserting article with duplicate ID fails."""
    init_database()

    ArticleRepository.insert_article(sample_article)

    # Try to insert again
    with pytest.raises(Exception):  # sqlite3.IntegrityError
        ArticleRepository.insert_article(sample_article)


def test_insert_articles_bulk(test_env, temp_database):
    """Test bulk article insertion."""
    init_database()

    articles = [
        RawArticle(
            id=f"test{i}",
            source_url=f"https://example.com/article{i}",
            source_name="Test Source",
            source_type=SourceType.RSS,
            title=f"Article {i}",
            content=f"Content {i}",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            content_hash=f"hash{i}",
            is_duplicate=False,
        )
        for i in range(5)
    ]

    inserted = ArticleRepository.insert_articles(articles)

    assert inserted == 5


def test_get_article_by_id_not_found(test_env, temp_database):
    """Test getting non-existent article returns None."""
    init_database()

    article = ArticleRepository.get_article_by_id("nonexistent")

    assert article is None


def test_get_recent_articles(test_env, temp_database):
    """Test getting recent articles."""
    init_database()

    # Insert 3 articles
    articles = [
        RawArticle(
            id=f"test{i}",
            source_url=f"https://example.com/{i}",
            source_name="Test",
            source_type=SourceType.RSS,
            title=f"Article {i}",
            content=f"Content {i}",
            published_at=datetime(2026, 7, i + 1, 12, 0, 0),
            fetched_at=datetime.now(),
            content_hash=f"hash{i}",
            is_duplicate=False,
        )
        for i in range(3)
    ]
    ArticleRepository.insert_articles(articles)

    recent = ArticleRepository.get_recent_articles(limit=2)

    assert len(recent) == 2
    # Should be ordered by published_at DESC
    assert recent[0].title == "Article 2"
    assert recent[1].title == "Article 1"


def test_count_articles(test_env, temp_database):
    """Test counting articles."""
    init_database()

    # Insert articles from different sources
    articles = [
        RawArticle(
            id=f"test{i}",
            source_url=f"https://example.com/{i}",
            source_name="Source A" if i < 2 else "Source B",
            source_type=SourceType.RSS,
            title=f"Article {i}",
            content=f"Content {i}",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            content_hash=f"hash{i}",
            is_duplicate=(i == 3),  # Mark one as duplicate
        )
        for i in range(4)
    ]
    ArticleRepository.insert_articles(articles)

    counts = ArticleRepository.count_articles()

    assert counts["total"] == 4
    assert counts["unique"] == 3
    assert counts["duplicates"] == 1
    assert counts["by_source"]["Source A"] == 2
    assert counts["by_source"]["Source B"] == 1
