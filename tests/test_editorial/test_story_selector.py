"""Tests for story selection."""

from datetime import datetime, timedelta

from src.core.schemas import RawArticle, SourceType
from src.editorial.story_selector import calculate_composite_score, select_top_stories


def create_test_article(article_id: str, hours_ago: int = 2) -> RawArticle:
    """Helper to create test article."""
    return RawArticle(
        id=article_id,
        source_url=f"https://example.com/{article_id}",
        source_name="Tagesschau",
        source_type=SourceType.RSS,
        title=f"Article {article_id}",
        content="Test content " * 50,
        published_at=datetime.now() - timedelta(hours=hours_ago),
        fetched_at=datetime.now(),
        content_hash=f"hash{article_id}",
    )


def test_composite_score_quality_component():
    """Test composite score includes quality component."""
    article = create_test_article("test1", hours_ago=2)

    score_high = calculate_composite_score(article, quality_score=0.9)
    score_low = calculate_composite_score(article, quality_score=0.5)

    assert score_high > score_low


def test_composite_score_recency_component():
    """Test composite score includes recency component."""
    recent = create_test_article("recent", hours_ago=1)
    old = create_test_article("old", hours_ago=20)

    # Same quality score
    score_recent = calculate_composite_score(recent, quality_score=0.8)
    score_old = calculate_composite_score(old, quality_score=0.8)

    assert score_recent > score_old


def test_select_top_stories_basic():
    """Test selecting top N stories."""
    articles = [
        create_test_article(f"article{i}", hours_ago=i) for i in range(10)
    ]

    top_5 = select_top_stories(articles, count=5)

    assert len(top_5) == 5
    # Should prioritize recent articles (lower hours_ago)
    assert top_5[0].id in ["article0", "article1", "article2"]


def test_select_top_stories_fewer_than_requested():
    """Test selection when fewer articles than requested."""
    articles = [create_test_article(f"article{i}") for i in range(3)]

    top_5 = select_top_stories(articles, count=5)

    assert len(top_5) == 3  # Returns all available


def test_select_top_stories_sorting():
    """Test stories are sorted by composite score."""
    articles = [
        create_test_article("old_article", hours_ago=20),
        create_test_article("recent_article", hours_ago=1),
        create_test_article("medium_article", hours_ago=10),
    ]

    top_3 = select_top_stories(articles, count=3)

    # Recent should be first (higher composite score)
    assert top_3[0].id == "recent_article"
