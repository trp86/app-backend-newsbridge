"""Combined processor for summarization + translation in one API call."""

import json
import time
from datetime import datetime

import google.generativeai as genai
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.schemas import Brief, Language, RawArticle, Translation
from src.editorial.combined_prompt import get_combined_prompt

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
def call_gemini_combined(model_name: str, prompt: str) -> str:
    """Call Gemini API for combined processing with retry logic.

    Args:
        model_name: Model name
        prompt: Combined prompt

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
                max_output_tokens=8192,  # Larger for combined response
            ),
        )

        latency_ms = int((time.time() - start_time) * 1000)

        result_text = response.text

        logger.info(
            "gemini.combined_success",
            model=model_name,
            latency_ms=latency_ms,
        )

        return result_text

    except Exception as e:
        logger.error("gemini.combined_failed", model=model_name, error=str(e))
        raise


def parse_combined_response(response: str) -> dict[str, str]:
    """Parse JSON combined response from Gemini.

    Args:
        response: Gemini response text

    Returns:
        Dictionary with 8 fields (4 English + 4 Odia)

    Raises:
        ValueError: If response is invalid
    """
    try:
        # Clean up response
        cleaned = response.strip()

        # Remove markdown code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        # Extract JSON
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1

        if start == -1:
            logger.error("parse.no_opening_brace", response=cleaned[:500])
            raise ValueError("No opening brace { found in response")

        if end == 0:
            logger.error("parse.no_closing_brace", response=cleaned[:500])
            raise ValueError(
                f"No closing brace }} found. Response may be truncated. Got {len(cleaned)} characters."
            )

        json_str = cleaned[start:end]
        data = json.loads(json_str)

        # Validate required fields
        required = [
            "english_title",
            "english_30",
            "english_111",
            "english_250",
            "odia_title",
            "odia_30",
            "odia_111",
            "odia_250",
        ]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        return data

    except json.JSONDecodeError as e:
        logger.error("parse.json_error", error=str(e), response=response[:300])
        raise ValueError(f"Invalid JSON in response: {e}")


def process_article_combined(
    article: RawArticle, target_language: Language = Language.ODIA
) -> tuple[Brief, Translation]:
    """Process article: summarize + translate in ONE API call.

    Args:
        article: Raw article to process
        target_language: Target language (default: Odia)

    Returns:
        Tuple of (Brief with English summaries, Translation with Odia)

    Raises:
        Exception: If processing fails after retries
    """
    settings = get_settings()
    configure_gemini()

    logger.info(
        "combined.started",
        article_id=article.id,
        source=article.source_name,
        target_language=target_language.value,
        title=article.title[:50],
    )

    # Generate combined prompt
    prompt = get_combined_prompt(article, target_language)

    # Call Gemini ONCE
    response = call_gemini_combined(
        model_name=settings.gemini_summarization_model,  # Use better model
        prompt=prompt,
    )

    # Parse response
    result = parse_combined_response(response)

    # Create Brief object (English)
    brief = Brief(
        id=f"brief_{article.id}",
        article_id=article.id,
        title=result["english_title"],
        summary_30=result["english_30"],
        summary_111=result["english_111"],
        summary_250=result["english_250"],
        category="General",
        quality_score=0.8,  # Placeholder
        model_used=settings.gemini_summarization_model,
        processed_at=datetime.now(),
    )

    # Create Translation object (Odia)
    translation = Translation(
        id=f"trans_{brief.id}_{target_language.value}",
        brief_id=brief.id,
        language=target_language,
        title=result["odia_title"],
        summary_30=result["odia_30"],
        summary_111=result["odia_111"],
        summary_250=result["odia_250"],
        model_used=settings.gemini_summarization_model,
        translated_at=datetime.now(),
    )

    logger.info(
        "combined.completed",
        article_id=article.id,
        brief_id=brief.id,
        translation_id=translation.id,
        model=settings.gemini_summarization_model,
    )

    return brief, translation


def process_articles_combined(
    articles: list[RawArticle], target_language: Language = Language.ODIA
) -> tuple[list[Brief], list[Translation]]:
    """Process multiple articles with combined approach.

    Args:
        articles: List of articles to process
        target_language: Target language (default: Odia)

    Returns:
        Tuple of (list of Briefs, list of Translations)
    """
    briefs = []
    translations = []

    for article in articles:
        try:
            brief, translation = process_article_combined(article, target_language)
            briefs.append(brief)
            translations.append(translation)
        except Exception as e:
            logger.error(
                "combined.article_failed",
                article_id=article.id,
                source=article.source_name,
                error=str(e),
            )
            continue

    logger.info(
        "combined.batch_completed",
        requested=len(articles),
        successful=len(briefs),
        failed=len(articles) - len(briefs),
    )

    return briefs, translations
