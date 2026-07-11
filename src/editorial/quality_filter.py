"""Article quality scoring and filtering."""

from datetime import datetime

import structlog

from src.core.config import get_settings
from src.core.schemas import RawArticle

logger = structlog.get_logger()

# Trusted news sources (higher credibility)
TRUSTED_SOURCES = {
    "Tagesschau",
    "Süddeutsche Zeitung",
    "Der Spiegel International",
    "Deutsche Welle World",
    "Handelsblatt Global",
    "Reuters",
    "BBC",
    "AP",
    "Guardian",
}

# Spam/low-quality keywords
SPAM_KEYWORDS = {
    "click here",
    "buy now",
    "limited offer",
    "act now",
    "free gift",
    "winner",
    "claim your",
    "unsubscribe",
}

# Important topic keywords (boost score)
IMPORTANT_TOPICS = {
    "climate",
    "economy",
    "technology",
    "science",
    "policy",
    "election",
    "research",
    "energy",
    "innovation",
    "international",
    "trade",
    "education",
    "health",
}


def calculate_quality_score(article: RawArticle) -> float:
    """Calculate quality score for an article (0.0 to 1.0).

    Scoring components:
    - Content relevance (40%): Important topics vs spam
    - Source credibility (20%): Trusted sources get higher scores
    - Content completeness (20%): Length and structure
    - Freshness (20%): Recent articles preferred

    Args:
        article: Article to score

    Returns:
        Quality score between 0.0 and 1.0
    """
    scores = []
    weights = [0.4, 0.2, 0.2, 0.2]

    # 1. Content Relevance (40%)
    content_lower = (article.title + " " + article.content).lower()

    # Check for spam
    has_spam = any(keyword in content_lower for keyword in SPAM_KEYWORDS)
    if has_spam:
        scores.append(0.2)
    # Check for important topics
    elif any(topic in content_lower for topic in IMPORTANT_TOPICS):
        scores.append(0.9)
    else:
        scores.append(0.6)

    # 2. Source Credibility (20%)
    if article.source_name in TRUSTED_SOURCES:
        scores.append(1.0)
    else:
        scores.append(0.5)

    # 3. Content Completeness (20%)
    content_length = len(article.content)
    if content_length > 500:
        scores.append(0.9)
    elif content_length > 200:
        scores.append(0.7)
    elif content_length > 50:
        scores.append(0.5)
    else:
        scores.append(0.3)

    # 4. Freshness (20%)
    hours_old = (datetime.now() - article.published_at).total_seconds() / 3600

    if hours_old < 6:
        scores.append(1.0)
    elif hours_old < 12:
        scores.append(0.9)
    elif hours_old < 24:
        scores.append(0.8)
    elif hours_old < 48:
        scores.append(0.6)
    else:
        scores.append(0.4)

    # Calculate weighted average
    quality_score = sum(s * w for s, w in zip(scores, weights))

    logger.debug(
        "quality.scored",
        article_id=article.id,
        source=article.source_name,
        score=round(quality_score, 2),
        age_hours=round(hours_old, 1),
    )

    return quality_score


def filter_high_quality(
    articles: list[RawArticle], min_score: float | None = None
) -> list[RawArticle]:
    """Filter articles by quality score.

    Args:
        articles: List of articles to filter
        min_score: Minimum quality score (uses config default if None)

    Returns:
        List of high-quality articles (score >= min_score)
    """
    settings = get_settings()
    threshold = min_score if min_score is not None else settings.min_quality_score

    # Calculate scores for all articles
    scored_articles = []
    for article in articles:
        score = calculate_quality_score(article)
        if score >= threshold:
            scored_articles.append(article)

    logger.info(
        "quality.filtered",
        total=len(articles),
        high_quality=len(scored_articles),
        filtered_out=len(articles) - len(scored_articles),
        threshold=threshold,
    )

    return scored_articles
