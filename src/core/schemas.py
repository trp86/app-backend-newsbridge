"""Pydantic models for Global Knowledge Brief."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SourceType(str, Enum):
    """Article source type."""

    RSS = "rss"
    API = "api"


class Language(str, Enum):
    """Supported languages."""

    ENGLISH = "en"
    ODIA = "or"
    HINDI = "hi"
    BENGALI = "bn"
    TELUGU = "te"
    KANNADA = "kn"
    TAMIL = "ta"


class PublishStatus(str, Enum):
    """Publication status."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class RawArticle(BaseModel):
    """Ingested article before processing."""

    id: str
    source_url: HttpUrl
    source_name: str
    source_type: SourceType
    title: str
    content: str
    published_at: datetime
    fetched_at: datetime
    content_hash: str
    is_duplicate: bool = False

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "abc123",
                "source_url": "https://www.reuters.com/world/article123",
                "source_name": "Reuters World",
                "source_type": "rss",
                "title": "Global Climate Summit Concludes",
                "content": "World leaders gathered...",
                "published_at": "2026-07-04T10:30:00Z",
                "fetched_at": "2026-07-04T11:00:00Z",
                "content_hash": "sha256:abc...",
                "is_duplicate": False,
            }
        }
    )


class Brief(BaseModel):
    """Processed English brief."""

    id: str
    article_id: str
    title: str
    summary_30: str = Field(max_length=300, description="~30 words")
    summary_111: str = Field(max_length=1000, description="~111 words")
    summary_250: str = Field(max_length=2500, description="~250 words")
    category: str
    quality_score: float = Field(ge=0.0, le=1.0)
    model_used: str
    processed_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "brief123",
                "article_id": "abc123",
                "title": "Climate Summit Sets New Targets",
                "summary_30": "World leaders agree on new climate targets at summit.",
                "summary_111": "At the global climate summit, leaders from 150 countries...",
                "summary_250": "The weeklong climate summit concluded with...",
                "category": "International",
                "quality_score": 0.92,
                "model_used": "google/gemini-flash-1.5",
                "processed_at": "2026-07-04T12:00:00Z",
            }
        }
    )


class Translation(BaseModel):
    """Translated brief."""

    id: str
    brief_id: str
    language: Language
    title: str
    summary_30: str
    summary_111: str
    summary_250: str
    model_used: str
    translated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "trans123",
                "brief_id": "brief123",
                "language": "or",
                "title": "ଜଳବାୟୁ ସମ୍ମିଳନୀ ନୂତନ ଲକ୍ଷ୍ୟ ସ୍ଥିର କଲା",
                "summary_30": "ବିଶ୍ୱ ନେତାମାନେ ସମ୍ମିଳନୀରେ...",
                "summary_111": "ବୈଶ୍ୱିକ ଜଳବାୟୁ ସମ୍ମିଳନୀରେ...",
                "summary_250": "ସପ୍ତାହ ବ୍ୟାପୀ ଜଳବାୟୁ ସମ୍ମିଳନୀ...",
                "model_used": "google/gemini-pro-1.5",
                "translated_at": "2026-07-04T13:00:00Z",
            }
        }
    )


class DailyBrief(BaseModel):
    """Final published brief."""

    id: str
    date: datetime
    language: Language
    stories: list[Translation] = Field(max_length=5, description="Top 5 stories")
    telegram_message_id: str | None = None
    publish_status: PublishStatus
    published_at: datetime | None = None
    error_message: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "pub123",
                "date": "2026-07-04T00:00:00Z",
                "language": "or",
                "stories": [],
                "telegram_message_id": "12345",
                "publish_status": "sent",
                "published_at": "2026-07-04T06:00:00Z",
                "error_message": None,
            }
        }
    )


class APICallLog(BaseModel):
    """API usage log for cost tracking."""

    id: str
    timestamp: datetime
    model_used: str
    operation: str = Field(pattern="^(summarize|translate)$")
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None
    latency_ms: int | None = None
    success: bool
    error_message: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "log123",
                "timestamp": "2026-07-04T12:00:00Z",
                "model_used": "google/gemini-flash-1.5",
                "operation": "summarize",
                "input_tokens": 2500,
                "output_tokens": 300,
                "cost_usd": 0.0,
                "latency_ms": 1250,
                "success": True,
                "error_message": None,
            }
        }
    )


class RSSSource(BaseModel):
    """RSS feed source configuration."""

    name: str
    url: HttpUrl
    priority: int = Field(ge=1, le=3, description="1=primary, 2=secondary, 3=fallback")
    expected_articles: int = Field(ge=1, description="Expected articles per day")
    enabled: bool = True

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Reuters World",
                "url": "https://www.reuters.com/world/rss",
                "priority": 1,
                "expected_articles": 30,
                "enabled": True,
            }
        }
    )
