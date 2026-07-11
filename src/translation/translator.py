"""Translation service using Google Gemini API."""

import json
import time
from datetime import datetime

import google.generativeai as genai
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.schemas import Brief, Language, Translation
from src.translation.glossary import get_glossary_instructions

logger = structlog.get_logger()


def configure_gemini() -> None:
    """Configure Gemini API with API key."""
    settings = get_settings()
    genai.configure(api_key=settings.gemini_api_key)


def get_translation_prompt(brief: Brief, target_language: Language) -> str:
    """Generate translation prompt for a brief.

    Args:
        brief: Brief to translate
        target_language: Target language (currently only Odia supported)

    Returns:
        Formatted prompt for translation
    """
    glossary = get_glossary_instructions()

    return f"""You are a professional translator specializing in news translation.

Translate these English news summaries to Odia (ଓଡ଼ିଆ).

IMPORTANT:
- Make the translation NATURAL and MEANINGFUL for Odia readers
- This is NOT word-for-word translation
- Use culturally appropriate Odia phrases
- Keep the tone neutral and journalistic
- Maintain the clarity and meaning

{glossary}

ENGLISH SUMMARIES TO TRANSLATE:

Title: {brief.title}

30-word summary:
{brief.summary_30}

111-word summary:
{brief.summary_111}

250-word summary:
{brief.summary_250}

---

CRITICAL: Return ONLY valid JSON. No markdown, no explanation, no extra text.
Start your response with {{ and end with }}

Format:
{{
  "title": "translated title in Odia",
  "summary_30": "30-word summary in Odia",
  "summary_111": "111-word summary in Odia",
  "summary_250": "250-word summary in Odia"
}}"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call_gemini_translation(model_name: str, prompt: str) -> str:
    """Call Gemini API for translation with retry logic.

    Args:
        model_name: Model name
        prompt: Translation prompt

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
                max_output_tokens=4096,
            ),
        )

        latency_ms = int((time.time() - start_time) * 1000)

        result_text = response.text

        logger.info(
            "gemini.translation_success",
            model=model_name,
            latency_ms=latency_ms,
        )

        return result_text

    except Exception as e:
        logger.error("gemini.translation_failed", model=model_name, error=str(e))
        raise


def parse_translation_response(response: str) -> dict[str, str]:
    """Parse JSON translation response from Gemini.

    Args:
        response: Gemini response text

    Returns:
        Dictionary with title, summary_30, summary_111, summary_250

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
            raise ValueError("No opening brace { found in translation response")

        if end == 0:
            logger.error("parse.no_closing_brace", response=cleaned[:500])
            raise ValueError(
                f"No closing brace }} found. Response may be truncated. Got {len(cleaned)} characters."
            )

        json_str = cleaned[start:end]
        data = json.loads(json_str)

        # Validate required fields
        required = ["title", "summary_30", "summary_111", "summary_250"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        return data

    except json.JSONDecodeError as e:
        logger.error("parse.json_error", error=str(e), response=response[:300])
        raise ValueError(f"Invalid JSON in translation response: {e}")


def translate_brief(brief: Brief, target_language: Language = Language.ODIA) -> Translation:
    """Translate a brief to target language.

    Args:
        brief: Brief to translate
        target_language: Target language (default: Odia)

    Returns:
        Translation object

    Raises:
        Exception: If translation fails after retries
    """
    settings = get_settings()
    configure_gemini()

    logger.info(
        "translation.started",
        brief_id=brief.id,
        target_language=target_language.value,
        title=brief.title[:50],
    )

    # Generate prompt
    prompt = get_translation_prompt(brief, target_language)

    # Call Gemini
    response = call_gemini_translation(
        model_name=settings.gemini_translation_model,
        prompt=prompt,
    )

    # Parse response
    translations = parse_translation_response(response)

    # Create Translation object
    translation = Translation(
        id=f"trans_{brief.id}_{target_language.value}",
        brief_id=brief.id,
        language=target_language,
        title=translations["title"],
        summary_30=translations["summary_30"],
        summary_111=translations["summary_111"],
        summary_250=translations["summary_250"],
        model_used=settings.gemini_translation_model,
        translated_at=datetime.now(),
    )

    logger.info(
        "translation.completed",
        brief_id=brief.id,
        translation_id=translation.id,
        language=target_language.value,
        model=settings.gemini_translation_model,
    )

    return translation


def translate_briefs(
    briefs: list[Brief], target_language: Language = Language.ODIA
) -> list[Translation]:
    """Translate multiple briefs.

    Args:
        briefs: List of briefs to translate
        target_language: Target language (default: Odia)

    Returns:
        List of translations (successful translations only)
    """
    translations = []

    for brief in briefs:
        try:
            translation = translate_brief(brief, target_language)
            translations.append(translation)
        except Exception as e:
            logger.error(
                "translation.brief_failed",
                brief_id=brief.id,
                target_language=target_language.value,
                error=str(e),
            )
            continue

    logger.info(
        "translation.batch_completed",
        requested=len(briefs),
        successful=len(translations),
        failed=len(briefs) - len(translations),
        language=target_language.value,
    )

    return translations
