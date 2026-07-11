"""FastAPI server for NewsBridge."""

from datetime import datetime
from typing import Optional

import structlog
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.database import check_database_health
from src.storage.brief_repository import BriefRepository
from src.storage.translation_repository import TranslationRepository

logger = structlog.get_logger()

app = FastAPI(
    title="NewsBridge API",
    description="API for accessing curated global news briefs",
    version="1.0.0",
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Production - Netlify
        "https://app-newsbridge.netlify.app",
        "https://app-react-newsbridge.netlify.app",
        # Local development
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://localhost:5173",  # Vite dev server
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ArticleResponse(BaseModel):
    """Response model for articles."""

    id: str
    source: str
    category: str
    publishedAt: str
    english: dict[str, str]
    translations: dict[str, dict[str, str]]


class ArticlesResponse(BaseModel):
    """Response model for articles list."""

    articles: list[ArticleResponse]
    metadata: dict


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "NewsBridge API",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health():
    """Detailed health check with database stats."""
    try:
        health_data = check_database_health()
        return {
            "status": "healthy",
            "database": health_data,
        }
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed")


@app.get("/api/articles", response_model=ArticlesResponse)
async def get_articles(
    limit: int = Query(default=20, ge=1, le=100),
    language: Optional[str] = Query(default=None, description="Language code (e.g., 'or' for Odia)"),
):
    """Get recent articles with briefs and translations.

    Args:
        limit: Maximum number of articles to return (1-100)
        language: Optional language code for translations

    Returns:
        ArticlesResponse with articles and metadata
    """
    try:
        # Fetch briefs from database
        briefs = BriefRepository.get_recent_briefs(limit=limit)
        logger.info("briefs_check", count=len(briefs))

        # Fallback to raw articles if no briefs available
        if not briefs:
            from src.storage.repository import ArticleRepository

            raw_articles = ArticleRepository.get_recent_articles(limit=limit)

            if not raw_articles:
                return ArticlesResponse(
                    articles=[],
                    metadata={
                        "totalArticles": 0,
                        "lastUpdated": datetime.utcnow().isoformat() + "Z",
                    },
                )

            # Convert raw articles to response format
            articles = []
            for article in raw_articles:
                # Extract first 30, 111, and 250 words from content
                words = article.content.split()
                summary_30 = " ".join(words[:30]) + ("..." if len(words) > 30 else "")
                summary_111 = " ".join(words[:111]) + ("..." if len(words) > 111 else "")
                summary_250 = " ".join(words[:250]) + ("..." if len(words) > 250 else "")

                articles.append(
                    ArticleResponse(
                        id=article.id,
                        source=article.source_name,
                        category="world",  # Default category for raw articles
                        publishedAt=article.published_at.isoformat() + "Z",
                        english={
                            "title": article.title,
                            "summary_30": summary_30,
                            "summary_111": summary_111,
                            "summary_250": summary_250,
                        },
                        translations={},
                    )
                )

            metadata = {
                "totalArticles": len(articles),
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
                "note": "Displaying raw articles (briefs not yet processed)",
            }

            logger.info("raw_articles_fetched", count=len(articles))

            return ArticlesResponse(articles=articles, metadata=metadata)

        # Build article responses
        # Fetch all translations in one query (N+1 optimization)
        brief_ids = [brief.id for brief in briefs]
        translations_by_brief = TranslationRepository.get_translations_by_briefs(brief_ids)
        logger.info("translations_bulk_check", brief_count=len(brief_ids))

        articles = []
        for brief in briefs:
            # Get translations for this brief from the bulk fetch
            translations = {}
            brief_translations = translations_by_brief.get(brief.id, [])

            for translation in brief_translations:
                translations[translation.language.value] = {
                    "title": translation.title,
                    "summary_30": translation.summary_30,
                    "summary_111": translation.summary_111,
                    "summary_250": translation.summary_250,
                }

            article = ArticleResponse(
                id=brief.id,
                source="Global News",  # You can enhance this by joining with articles table
                category=brief.category,
                publishedAt=brief.processed_at.isoformat() + "Z",
                english={
                    "title": brief.title,
                    "summary_30": brief.summary_30,
                    "summary_111": brief.summary_111,
                    "summary_250": brief.summary_250,
                },
                translations=translations,
            )
            articles.append(article)

        metadata = {
            "totalArticles": len(articles),
            "lastUpdated": datetime.utcnow().isoformat() + "Z",
        }

        logger.info("articles_fetched", count=len(articles), language=language)

        return ArticlesResponse(articles=articles, metadata=metadata)

    except Exception as e:
        logger.error("get_articles_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch articles: {str(e)}")


@app.get("/api/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: str,
    language: Optional[str] = Query(default=None, description="Language code (e.g., 'or' for Odia)"),
):
    """Get a single article by ID.

    Args:
        article_id: Brief ID
        language: Optional language code for translation

    Returns:
        ArticleResponse with article details
    """
    try:
        # Fetch brief
        brief = BriefRepository.get_brief_by_id(article_id)

        if not brief:
            raise HTTPException(status_code=404, detail=f"Article {article_id} not found")

        # Get all translations for this brief
        translations = {}
        brief_translations = TranslationRepository.get_translations_by_brief(brief_id=brief.id)
        for translation in brief_translations:
            translations[translation.language.value] = {
                "title": translation.title,
                "summary_30": translation.summary_30,
                "summary_111": translation.summary_111,
                "summary_250": translation.summary_250,
            }

        article = ArticleResponse(
            id=brief.id,
            source="Global News",
            category=brief.category,
            publishedAt=brief.processed_at.isoformat() + "Z",
            english={
                "title": brief.title,
                "summary_30": brief.summary_30,
                "summary_111": brief.summary_111,
                "summary_250": brief.summary_250,
            },
            translations=translations,
        )

        logger.info("article_fetched", article_id=article_id, language=language)

        return article

    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_article_failed", article_id=article_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch article: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
