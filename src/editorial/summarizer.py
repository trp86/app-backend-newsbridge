"""Article summarization using Google Gemini API."""

import json
import time
from datetime import datetime

import google.generativeai as genai
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.schemas import Brief, RawArticle
from src.editorial.prompts import get_summarization_prompt

logger = structlog.get_logger()


def configure_gemini() -> None:
    """Configure Gemini API with API key."""
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call_gemini_with_retry(model_name: str, prompt: str) -> str:
    """Call Gemini API with retry logic.

    Args:
        model_name: Model name (e.g., gemini-1.5-flash)
        prompt: Prompt text

    Returns:
        Gemini response text

    Raises:
        Exception: If all retries fail
    """
    start_time = time.time()

    try:
        model = genai.GenerativeModel(model_name)

        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4096,  # Increased for longer responses
            ),
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract text from response
        result_text = response.text

        logger.info(
            "gemini.success",
            model=model_name,
            latency_ms=latency_ms,
        )

        return result_text

    except Exception as e:
        logger.error("gemini.failed", model=model_name, error=str(e))
        raise


def parse_summary_response(response: str) -> dict[str, str]:
    """Parse JSON response from Gemini.

    Args:
        response: Gemini response text (should be JSON)

    Returns:
        Dictionary with summary_30, summary_111, summary_250

    Raises:
        ValueError: If response is not valid JSON or missing fields
    """
    try:
        # Clean up response - remove markdown code blocks
        cleaned = response.strip()

        # Remove markdown JSON code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]  # Remove ```

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]  # Remove trailing ```

        cleaned = cleaned.strip()

        # Try to extract JSON object
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1

        if start == -1:
            logger.error("parse.no_opening_brace", response=cleaned[:500])
            raise ValueError("No opening brace { found in response")

        if end == 0:
            logger.error("parse.no_closing_brace", response=cleaned[:500], has_opening=True)
            raise ValueError(f"No closing brace }} found in response. Response may be truncated. Got {len(cleaned)} characters.")

        json_str = cleaned[start:end]
        data = json.loads(json_str)

        # Validate required fields
        required = ["summary_30", "summary_111", "summary_250"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        return data

    except json.JSONDecodeError as e:
        logger.error("parse.json_error", error=str(e), response=response[:300])
        raise ValueError(f"Invalid JSON response: {e}")


def summarize_article(article: RawArticle) -> Brief:
    """Summarize article into 30/111/250 word summaries.

    For German articles: meaningful transformation to English
    For English articles: standard summarization

    Args:
        article: Raw article to summarize

    Returns:
        Brief with 3 summaries

    Raises:
        Exception: If summarization fails after retries
    """
    settings = get_settings()
    configure_gemini()

    logger.info(
        "summarize.started",
        article_id=article.id,
        source=article.source_name,
        title=article.title[:50],
    )

    # Generate prompt based on language
    prompt = get_summarization_prompt(
        article_title=article.title,
        article_content=article.content,
        source_name=article.source_name,
    )

    # Call Gemini
    response = call_gemini_with_retry(
        model_name=settings.gemini_summarization_model,
        prompt=prompt,
    )

    # Parse response
    summaries = parse_summary_response(response)

    # Create Brief object
    brief = Brief(
        id=f"brief_{article.id}",
        article_id=article.id,
        title=summaries["summary_30"][:100],  # Use first part of headline as title
        summary_30=summaries["summary_30"],
        summary_111=summaries["summary_111"],
        summary_250=summaries["summary_250"],
        category="General",  # TODO: Implement category detection
        quality_score=0.8,  # Placeholder - will be calculated by quality_filter
        model_used=settings.gemini_summarization_model,
        processed_at=datetime.now(),
    )

    logger.info(
        "summarize.completed",
        article_id=article.id,
        brief_id=brief.id,
        model=settings.gemini_summarization_model,
    )

    return brief


def summarize_articles(articles: list[RawArticle]) -> list[Brief]:
    """Summarize multiple articles.

    Args:
        articles: List of articles to summarize

    Returns:
        List of briefs (successful summarizations only)
    """
    briefs = []

    for article in articles:
        try:
            brief = summarize_article(article)
            briefs.append(brief)
        except Exception as e:
            logger.error(
                "summarize.article_failed",
                article_id=article.id,
                source=article.source_name,
                error=str(e),
            )
            continue

    logger.info(
        "summarize.batch_completed",
        requested=len(articles),
        successful=len(briefs),
        failed=len(articles) - len(briefs),
    )

    return briefs
