"""Story selection - pick top N stories for daily brief."""

from datetime import datetime

import structlog

from src.core.config import get_settings
from src.core.schemas import RawArticle
from src.editorial.quality_filter import calculate_quality_score

logger = structlog.get_logger()


def calculate_composite_score(article: RawArticle, quality_score: float) -> float:
    """Calculate composite score for story selection.

    Combines:
    - Quality score (60%): Article quality
    - Recency (30%): How fresh the news is
    - Diversity (10%): Category balance (future)

    Args:
        article: Article to score
        quality_score: Pre-calculated quality score

    Returns:
        Composite score for ranking
    """
    # Quality component (60%)
    quality_component = quality_score * 0.6

    # Recency component (30%)
    hours_old = (datetime.now() - article.published_at).total_seconds() / 3600
    # Score decays over 24 hours
    recency_score = max(0, 1 - (hours_old / 24))
    recency_component = recency_score * 0.3

    # Diversity component (10%) - placeholder for now
    # TODO: Implement category-based diversity scoring
    diversity_component = 0.1

    composite = quality_component + recency_component + diversity_component

    return composite


def select_top_stories(
    articles: list[RawArticle], count: int | None = None
) -> list[RawArticle]:
    """Select top N stories by composite score.

    Args:
        articles: List of articles to select from
        count: Number of stories to select (uses config default if None)

    Returns:
        List of top N articles, sorted by composite score (highest first)

    Example:
        top_5 = select_top_stories(articles, count=5)
    """
    settings = get_settings()
    n = count if count is not None else settings.top_stories_count

    # Calculate composite scores
    scored = []
    for article in articles:
        quality_score = calculate_quality_score(article)
        composite_score = calculate_composite_score(article, quality_score)

        scored.append((article, composite_score, quality_score))

        logger.debug(
            "selection.scored",
            article_id=article.id,
            title=article.title[:50],
            quality=round(quality_score, 2),
            composite=round(composite_score, 2),
        )

    # Sort by composite score (highest first)
    scored.sort(key=lambda x: x[1], reverse=True)

    # Select top N
    top_articles = [article for article, _, _ in scored[:n]]

    logger.info(
        "selection.completed",
        total_articles=len(articles),
        selected=len(top_articles),
        selected_all=len(articles) <= n,
        top_score=round(scored[0][1], 2) if scored else 0,
        cutoff_score=round(scored[min(n - 1, len(scored) - 1)][1], 2) if scored else 0,
    )

    return top_articles


def select_with_diversity(
    articles: list[RawArticle], count: int | None = None
) -> list[RawArticle]:
    """Select top stories with category diversity.

    TODO: Implement category-aware selection
    - Ensure mix of topics (politics, tech, economy, science)
    - Avoid multiple stories on same topic
    - Balance German vs English sources

    Args:
        articles: List of articles
        count: Number to select

    Returns:
        Diverse selection of top articles
    """
    # For now, fallback to simple selection
    # Will implement diversity logic in future iteration
    logger.warning("selection.diversity_not_implemented")
    return select_top_stories(articles, count)
