"""Tests for quality filtering."""

from datetime import datetime, timedelta

from src.core.schemas import RawArticle, SourceType
from src.editorial.quality_filter import calculate_quality_score, filter_high_quality


def create_test_article(
    title="Test Article",
    content="Test content here",
    source_name="Tagesschau",
    published_hours_ago=2,
) -> RawArticle:
    """Helper to create test article."""
    return RawArticle(
        id="test123",
        source_url="https://example.com/article",
        source_name=source_name,
        source_type=SourceType.RSS,
        title=title,
        content=content,
        published_at=datetime.now() - timedelta(hours=published_hours_ago),
        fetched_at=datetime.now(),
        content_hash="abc123",
    )


def test_quality_score_trusted_source():
    """Test quality score for trusted source."""
    article = create_test_article(
        source_name="Tagesschau",
        content="This is a long article about climate policy " * 50,
        published_hours_ago=1,
    )

    score = calculate_quality_score(article)

    assert score >= 0.8  # Should be high quality
    assert score <= 1.0


def test_quality_score_untrusted_source():
    """Test quality score for unknown source."""
    article = create_test_article(
        source_name="Unknown Blog",
        content="Short content",
        published_hours_ago=48,
    )

    score = calculate_quality_score(article)

    assert score < 0.7  # Should be lower quality


def test_quality_score_spam_content():
    """Test quality score for spam content."""
    article = create_test_article(
        title="Click here to buy now!",
        content="Limited offer! Act now and claim your free gift!",
        source_name="Spam Site",
    )

    score = calculate_quality_score(article)

    assert score < 0.5  # Should be low quality


def test_quality_score_important_topics():
    """Test quality score boost for important topics."""
    article = create_test_article(
        title="Climate Policy Changes",
        content="New research on renewable energy technology and climate innovation " * 20,
        source_name="Tagesschau",
        published_hours_ago=1,
    )

    score = calculate_quality_score(article)

    assert score >= 0.85  # Should be very high quality


def test_quality_score_freshness():
    """Test quality score varies with article age."""
    recent = create_test_article(published_hours_ago=1)
    old = create_test_article(published_hours_ago=50)

    recent_score = calculate_quality_score(recent)
    old_score = calculate_quality_score(old)

    assert recent_score > old_score


def test_filter_high_quality():
    """Test filtering articles by quality."""
    articles = [
        create_test_article(
            title="Good Article",
            content="Climate policy changes " * 50,
            source_name="Tagesschau",
            published_hours_ago=1,
        ),
        create_test_article(
            title="Spam Article",
            content="Click here! Buy now!",
            source_name="Spam",
            published_hours_ago=50,
        ),
        create_test_article(
            title="Decent Article",
            content="Economy report " * 30,
            source_name="Deutsche Welle World",
            published_hours_ago=5,
        ),
    ]

    high_quality = filter_high_quality(articles, min_score=0.7)

    assert len(high_quality) < len(articles)
    assert len(high_quality) >= 1  # At least the good article should pass
