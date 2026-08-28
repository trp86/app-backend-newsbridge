"""Translation service using Google Gemini API."""

import json
import time
from datetime import datetime

from google import genai
from google.genai import types
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import get_settings
from src.core.schemas import Brief, Language, Translation
from src.translation.glossary import get_glossary_instructions

logger = structlog.get_logger()

LANGUAGE_DISPLAY_NAMES: dict[Language, str] = {
    Language.ENGLISH: "English",
    Language.ODIA: "Odia (ଓଡ଼ିଆ)",
    Language.HINDI: "Hindi (हिंदी)",
    Language.TAMIL: "Tamil (தமிழ்)",
    Language.KANNADA: "Kannada (ಕನ್ನಡ)",
    Language.SPANISH: "Spanish (Español)",
    Language.CANTONESE: "Cantonese (廣東話)",
    Language.MALAY: "Bahasa Melayu",
    Language.DUTCH: "Dutch (Nederlands)",
    Language.TURKISH: "Turkish (Türkçe)",
    Language.ARABIC: "Arabic (العربية)",
    Language.BENGALI: "Bengali (বাংলা)",
    Language.TELUGU: "Telugu (తెలుగు)",
}

ALL_TARGET_LANGUAGES: list[Language] = [
    Language.ENGLISH,
    Language.ODIA,
    Language.HINDI,
    Language.TAMIL,
    Language.KANNADA,
    Language.SPANISH,
    Language.CANTONESE,
    Language.MALAY,
    Language.DUTCH,
    Language.TURKISH,
    Language.ARABIC,
]


def _get_gemini_client() -> genai.Client:
    settings = get_settings()
    return genai.Client(api_key=settings.gemini_api_key)


def get_translation_prompt(brief: Brief, target_language: Language) -> str:
    """Generate translation prompt for a single target language."""
    lang_name = LANGUAGE_DISPLAY_NAMES.get(target_language, target_language.value)
    glossary = get_glossary_instructions()

    return f"""You are a professional translator specializing in news translation.

Translate these English news summaries to {lang_name}.

IMPORTANT:
- Make the translation NATURAL and MEANINGFUL for {lang_name} readers
- This is NOT word-for-word translation
- Use culturally appropriate phrases
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
  "title": "translated title in {lang_name}",
  "summary_30": "30-word summary in {lang_name}",
  "summary_111": "111-word summary in {lang_name}",
  "summary_250": "250-word summary in {lang_name}"
}}"""


def get_batch_translation_prompt(brief: Brief, target_languages: list[Language]) -> str:
    """Generate a single prompt to translate into all target languages at once."""
    lang_list = "\n".join(
        f"- {LANGUAGE_DISPLAY_NAMES[lang]} (code: {lang.value})"
        for lang in target_languages
    )
    glossary = get_glossary_instructions()

    example_entries = ",\n".join(
        f'  "{lang.value}": {{"title": "...", "summary_30": "...", "summary_111": "...", "summary_250": "..."}}'
        for lang in target_languages
    )
    example_json = "{\n" + example_entries + "\n}"

    return f"""You are a professional translator specializing in news translation.

Translate these English news summaries into ALL of the following languages simultaneously:

{lang_list}

IMPORTANT:
- Make each translation NATURAL and MEANINGFUL for native readers of that language
- This is NOT word-for-word translation
- Use culturally appropriate phrases for each language
- Keep the tone neutral and journalistic
- Maintain the clarity and meaning across all languages
- For right-to-left languages (Arabic): use correct text direction

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
Use the language code (shown in parentheses above) as the key for each entry.
Start your response with {{ and end with }}

Format:
{example_json}"""


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
def call_gemini_translation(model_name: str, prompt: str) -> str:
    """Call Gemini API for translation with retry logic."""
    start_time = time.time()

    try:
        client = _get_gemini_client()

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=8192,
            ),
        )

        latency_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "gemini.translation_success",
            model=model_name,
            latency_ms=latency_ms,
        )

        return response.text

    except Exception as e:
        logger.error("gemini.translation_failed", model=model_name, error=str(e))
        raise


def _clean_json_response(response: str) -> str:
    """Strip markdown fences and whitespace from a Gemini JSON response."""
    cleaned = response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start == -1:
        raise ValueError("No opening brace { found in response")
    if end == 0:
        raise ValueError(f"No closing brace }} found. Response may be truncated ({len(cleaned)} chars).")
    return cleaned[start:end]


def parse_translation_response(response: str) -> dict[str, str]:
    """Parse single-language JSON translation response from Gemini."""
    try:
        data = json.loads(_clean_json_response(response))
        for field in ("title", "summary_30", "summary_111", "summary_250"):
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        return data
    except json.JSONDecodeError as e:
        logger.error("parse.json_error", error=str(e), response=response[:300])
        raise ValueError(f"Invalid JSON in translation response: {e}")


def parse_batch_translation_response(
    response: str, target_languages: list[Language]
) -> dict[Language, dict[str, str]]:
    """Parse a batch JSON response containing translations for multiple languages."""
    try:
        data = json.loads(_clean_json_response(response))
        result: dict[Language, dict[str, str]] = {}

        for lang in target_languages:
            if lang.value not in data:
                logger.warning("parse.missing_language", language=lang.value)
                continue
            entry = data[lang.value]
            for field in ("title", "summary_30", "summary_111", "summary_250"):
                if field not in entry:
                    raise ValueError(f"Missing field '{field}' for language '{lang.value}'")
            result[lang] = entry

        return result

    except json.JSONDecodeError as e:
        logger.error("parse.batch_json_error", error=str(e), response=response[:300])
        raise ValueError(f"Invalid JSON in batch translation response: {e}")


def translate_brief(brief: Brief, target_language: Language = Language.ODIA) -> Translation:
    """Translate a brief to a single target language."""
    settings = get_settings()

    logger.info(
        "translation.started",
        brief_id=brief.id,
        target_language=target_language.value,
        title=brief.title[:50],
    )

    prompt = get_translation_prompt(brief, target_language)
    response = call_gemini_translation(model_name=settings.gemini_translation_model, prompt=prompt)
    translations = parse_translation_response(response)

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


def translate_brief_batch(
    brief: Brief,
    target_languages: list[Language] | None = None,
) -> dict[Language, Translation]:
    """Translate a brief into all target languages in a single Gemini API call.

    English is handled as a pass-through (no API call needed).
    All other languages are translated together in one request.

    Returns:
        dict mapping Language -> Translation for each requested language
    """
    if target_languages is None:
        target_languages = ALL_TARGET_LANGUAGES

    settings = get_settings()

    result: dict[Language, Translation] = {}

    # English: pass-through from the brief (already in English)
    if Language.ENGLISH in target_languages:
        result[Language.ENGLISH] = Translation(
            id=f"trans_{brief.id}_{Language.ENGLISH.value}",
            brief_id=brief.id,
            language=Language.ENGLISH,
            title=brief.title,
            summary_30=brief.summary_30,
            summary_111=brief.summary_111,
            summary_250=brief.summary_250,
            model_used="passthrough",
            translated_at=datetime.now(),
        )

    non_english = [lang for lang in target_languages if lang != Language.ENGLISH]
    if not non_english:
        return result

    logger.info(
        "translation.batch_started",
        brief_id=brief.id,
        languages=[lang.value for lang in non_english],
        title=brief.title[:50],
    )

    prompt = get_batch_translation_prompt(brief, non_english)
    response = call_gemini_translation(model_name=settings.gemini_translation_model, prompt=prompt)
    translations_data = parse_batch_translation_response(response, non_english)

    for lang, data in translations_data.items():
        result[lang] = Translation(
            id=f"trans_{brief.id}_{lang.value}",
            brief_id=brief.id,
            language=lang,
            title=data["title"],
            summary_30=data["summary_30"],
            summary_111=data["summary_111"],
            summary_250=data["summary_250"],
            model_used=settings.gemini_translation_model,
            translated_at=datetime.now(),
        )

    logger.info(
        "translation.batch_completed",
        brief_id=brief.id,
        requested=len(non_english),
        successful=len(translations_data),
        failed=len(non_english) - len(translations_data),
    )

    return result


def translate_briefs(
    briefs: list[Brief], target_language: Language = Language.ODIA
) -> list[Translation]:
    """Translate multiple briefs to a single target language."""
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

    logger.info(
        "translation.batch_completed",
        requested=len(briefs),
        successful=len(translations),
        failed=len(briefs) - len(translations),
        language=target_language.value,
    )

    return translations


def translate_briefs_batch(
    briefs: list[Brief],
    target_languages: list[Language] | None = None,
) -> dict[str, dict[Language, Translation]]:
    """Translate multiple briefs into all target languages.

    Makes one Gemini API call per brief (not per language).

    Returns:
        dict mapping brief_id -> {Language -> Translation}
    """
    if target_languages is None:
        target_languages = ALL_TARGET_LANGUAGES

    results: dict[str, dict[Language, Translation]] = {}

    for brief in briefs:
        try:
            results[brief.id] = translate_brief_batch(brief, target_languages)
        except Exception as e:
            logger.error(
                "translation.brief_batch_failed",
                brief_id=brief.id,
                error=str(e),
            )

    logger.info(
        "translation.briefs_batch_completed",
        requested=len(briefs),
        successful=len(results),
        failed=len(briefs) - len(results),
    )

    return results
