"""Tests for Pydantic schemas."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from src.core.schemas import (
    Brief,
    Language,
    PublishStatus,
    RawArticle,
    RSSSource,
    SourceType,
    Translation,
)


def test_raw_article_valid():
    """Test valid RawArticle creation."""
    article = RawArticle(
        id="test123",
        source_url="https://www.reuters.com/world/test",
        source_name="Reuters",
        source_type=SourceType.RSS,
        title="Test Article",
        content="Test content here",
        published_at=datetime.now(),
        fetched_at=datetime.now(),
        content_hash="abc123",
    )
    assert article.source_type == SourceType.RSS
    assert article.is_duplicate is False


def test_raw_article_invalid_url():
    """Test RawArticle with invalid URL fails validation."""
    with pytest.raises(ValidationError):
        RawArticle(
            id="test123",
            source_url="not-a-valid-url",
            source_name="Reuters",
            source_type=SourceType.RSS,
            title="Test",
            content="Content",
            published_at=datetime.now(),
            fetched_at=datetime.now(),
            content_hash="abc",
        )


def test_brief_quality_score_bounds():
    """Test Brief quality_score must be between 0 and 1."""
    with pytest.raises(ValidationError):
        Brief(
            id="brief123",
            article_id="art123",
            title="Test",
            summary_30="Short summary",
            summary_111="Medium summary " * 10,
            summary_250="Long summary " * 20,
            category="Technology",
            quality_score=1.5,  # Invalid: > 1
            model_used="test-model",
            processed_at=datetime.now(),
        )


def test_brief_valid():
    """Test valid Brief creation."""
    brief = Brief(
        id="brief123",
        article_id="art123",
        title="Test Brief",
        summary_30="This is a test summary.",
        summary_111="This is a longer test summary. " * 8,
        summary_250="This is the longest test summary. " * 20,
        category="Science",
        quality_score=0.85,
        model_used="google/gemini-flash-1.5",
        processed_at=datetime.now(),
    )
    assert brief.quality_score == 0.85
    assert brief.category == "Science"


def test_translation_language_enum():
    """Test Translation uses Language enum correctly."""
    translation = Translation(
        id="trans123",
        brief_id="brief123",
        language=Language.ODIA,
        title="ଓଡିଆ ଶିରୋନାମା",
        summary_30="ସଂକ୍ଷିପ୍ତ ସାରାଂଶ",
        summary_111="ମଧ୍ୟମ ସାରାଂଶ " * 10,
        summary_250="ବିସ୍ତୃତ ସାରାଂଶ " * 20,
        model_used="google/gemini-pro-1.5",
        translated_at=datetime.now(),
    )
    assert translation.language == Language.ODIA
    assert translation.language.value == "or"


def test_rss_source_priority_bounds():
    """Test RSSSource priority must be between 1 and 3."""
    with pytest.raises(ValidationError):
        RSSSource(
            name="Test Source",
            url="https://example.com/rss",
            priority=5,  # Invalid: > 3
            expected_articles=10,
        )


def test_rss_source_valid():
    """Test valid RSSSource creation."""
    source = RSSSource(
        name="Reuters",
        url="https://www.reuters.com/world/rss",
        priority=1,
        expected_articles=30,
    )
    assert source.priority == 1
    assert source.enabled is True


def test_publish_status_enum():
    """Test PublishStatus enum values."""
    assert PublishStatus.PENDING.value == "pending"
    assert PublishStatus.SENT.value == "sent"
    assert PublishStatus.FAILED.value == "failed"
