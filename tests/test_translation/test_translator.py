"""Tests for multi-language translation — all 11 target languages."""

import json
from datetime import datetime
from unittest.mock import patch

import pytest

from src.core.schemas import Brief, Language, Translation
from src.translation.translator import (
    ALL_TARGET_LANGUAGES,
    LANGUAGE_DISPLAY_NAMES,
    get_batch_translation_prompt,
    get_translation_prompt,
    parse_batch_translation_response,
    parse_translation_response,
    translate_brief_batch,
)


@pytest.fixture
def sample_brief():
    return Brief(
        id="brief_test_001",
        article_id="art_001",
        title="German Chancellor announces new climate policy",
        summary_30="Germany's Chancellor announced a new climate policy targeting carbon neutrality by 2045.",
        summary_111=(
            "Germany's Chancellor revealed a landmark climate policy on Tuesday, setting an "
            "ambitious target of carbon neutrality by 2045. The plan includes phasing out coal "
            "by 2030, increasing renewable energy subsidies, and introducing a carbon tax on "
            "heavy industry. Business groups expressed concern over the economic impact."
        ),
        summary_250=(
            "Germany's Chancellor announced a comprehensive climate policy on Tuesday that sets "
            "the country on a path to carbon neutrality by 2045. The landmark plan includes "
            "phasing out all coal power by 2030, significantly increasing renewable energy "
            "subsidies, and introducing a new carbon tax on heavy industries. Environmental "
            "groups broadly welcomed the announcement. However, business groups expressed "
            "concern over potential job losses. The government pledged to create a transition "
            "fund to support workers in coal regions and invest in green technology."
        ),
        category="Politics",
        quality_score=0.88,
        model_used="gemini-2.5-flash",
        processed_at=datetime.now(),
    )


# ---------------------------------------------------------------------------
# Language enum coverage
# ---------------------------------------------------------------------------

def test_all_11_languages_present_in_enum():
    expected_codes = {"en", "or", "hi", "ta", "kn", "es", "yue", "ms", "nl", "tr", "ar"}
    actual_codes = {lang.value for lang in ALL_TARGET_LANGUAGES}
    missing = expected_codes - actual_codes
    assert not missing, f"Missing language codes: {missing}"


def test_all_language_enum_values():
    assert Language.ENGLISH.value == "en"
    assert Language.ODIA.value == "or"
    assert Language.HINDI.value == "hi"
    assert Language.TAMIL.value == "ta"
    assert Language.KANNADA.value == "kn"
    assert Language.SPANISH.value == "es"
    assert Language.CANTONESE.value == "yue"
    assert Language.MALAY.value == "ms"
    assert Language.DUTCH.value == "nl"
    assert Language.TURKISH.value == "tr"
    assert Language.ARABIC.value == "ar"


def test_all_target_languages_have_display_names():
    for lang in ALL_TARGET_LANGUAGES:
        assert lang in LANGUAGE_DISPLAY_NAMES, f"No display name for {lang.value}"
        assert len(LANGUAGE_DISPLAY_NAMES[lang]) > 0, f"Empty display name for {lang.value}"


# ---------------------------------------------------------------------------
# Single-language prompt tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lang", [l for l in ALL_TARGET_LANGUAGES if l != Language.ENGLISH])
def test_single_prompt_uses_correct_language_name(sample_brief, lang):
    prompt = get_translation_prompt(sample_brief, lang)
    lang_name = LANGUAGE_DISPLAY_NAMES[lang]
    assert lang_name in prompt, f"Expected '{lang_name}' in prompt for {lang.value}"


@pytest.mark.parametrize("lang", [l for l in ALL_TARGET_LANGUAGES if l != Language.ENGLISH])
def test_single_prompt_not_hardcoded_to_odia(sample_brief, lang):
    if lang == Language.ODIA:
        return
    prompt = get_translation_prompt(sample_brief, lang)
    assert "Translate these English news summaries to Odia" not in prompt, \
        f"Prompt for {lang.value} is still hardcoded to Odia"


def test_single_prompt_contains_article_content(sample_brief):
    prompt = get_translation_prompt(sample_brief, Language.HINDI)
    assert sample_brief.title in prompt
    assert sample_brief.summary_30 in prompt
    assert sample_brief.summary_111 in prompt
    assert sample_brief.summary_250 in prompt


# ---------------------------------------------------------------------------
# Batch prompt tests
# ---------------------------------------------------------------------------

def test_batch_prompt_contains_all_language_codes(sample_brief):
    non_english = [l for l in ALL_TARGET_LANGUAGES if l != Language.ENGLISH]
    prompt = get_batch_translation_prompt(sample_brief, non_english)
    for lang in non_english:
        assert lang.value in prompt, f"Language code '{lang.value}' missing from batch prompt"


def test_batch_prompt_contains_article_content(sample_brief):
    non_english = [l for l in ALL_TARGET_LANGUAGES if l != Language.ENGLISH]
    prompt = get_batch_translation_prompt(sample_brief, non_english)
    assert sample_brief.title in prompt
    assert sample_brief.summary_30 in prompt


# ---------------------------------------------------------------------------
# Parse tests
# ---------------------------------------------------------------------------

def test_parse_single_response_valid():
    response = json.dumps({
        "title": "जर्मन चांसलर ने नई जलवायु नीति की घोषणा की",
        "summary_30": "जर्मनी ने 2045 तक कार्बन तटस्थता का लक्ष्य रखा।",
        "summary_111": "जर्मनी के चांसलर ने मंगलवार को नीति की घोषणा की।",
        "summary_250": "जर्मनी के चांसलर ने एक व्यापक जलवायु नीति की घोषणा की।",
    })
    result = parse_translation_response(response)
    assert result["title"] == "जर्मन चांसलर ने नई जलवायु नीति की घोषणा की"


def test_parse_single_response_strips_markdown():
    raw = '```json\n{"title":"t","summary_30":"s","summary_111":"m","summary_250":"l"}\n```'
    result = parse_translation_response(raw)
    assert result["title"] == "t"


def test_parse_single_response_missing_field_raises():
    bad = json.dumps({"title": "t", "summary_30": "s"})  # missing summary_111 and summary_250
    with pytest.raises(ValueError, match="Missing required field"):
        parse_translation_response(bad)


def test_parse_batch_response_all_languages():
    non_english = [l for l in ALL_TARGET_LANGUAGES if l != Language.ENGLISH]
    mock_data = {
        lang.value: {
            "title": f"title_{lang.value}",
            "summary_30": f"s30_{lang.value}",
            "summary_111": f"s111_{lang.value}",
            "summary_250": f"s250_{lang.value}",
        }
        for lang in non_english
    }
    result = parse_batch_translation_response(json.dumps(mock_data), non_english)
    assert len(result) == len(non_english)
    for lang in non_english:
        assert lang in result
        assert result[lang]["title"] == f"title_{lang.value}"


def test_parse_batch_response_missing_language_skipped():
    non_english = [Language.HINDI, Language.ARABIC]
    mock_data = {
        "hi": {"title": "t", "summary_30": "s", "summary_111": "m", "summary_250": "l"},
        # Arabic missing — should be skipped, not raise
    }
    result = parse_batch_translation_response(json.dumps(mock_data), non_english)
    assert Language.HINDI in result
    assert Language.ARABIC not in result


def test_parse_batch_response_strips_markdown():
    non_english = [Language.HINDI]
    mock_data = {"hi": {"title": "t", "summary_30": "s", "summary_111": "m", "summary_250": "l"}}
    raw = f"```json\n{json.dumps(mock_data)}\n```"
    result = parse_batch_translation_response(raw, non_english)
    assert Language.HINDI in result


# ---------------------------------------------------------------------------
# translate_brief_batch unit tests (Gemini mocked)
# ---------------------------------------------------------------------------

def test_english_passthrough_skips_api_call(sample_brief):
    with patch("src.translation.translator.call_gemini_translation") as mock_api:
        result = translate_brief_batch(sample_brief, [Language.ENGLISH])
    mock_api.assert_not_called()
    assert Language.ENGLISH in result
    assert result[Language.ENGLISH].title == sample_brief.title
    assert result[Language.ENGLISH].summary_30 == sample_brief.summary_30
    assert result[Language.ENGLISH].model_used == "passthrough"


def test_batch_makes_single_api_call_for_all_languages(sample_brief):
    non_english = [l for l in ALL_TARGET_LANGUAGES if l != Language.ENGLISH]
    mock_response = json.dumps({
        lang.value: {
            "title": f"title_{lang.value}",
            "summary_30": f"s30_{lang.value}",
            "summary_111": f"s111_{lang.value}",
            "summary_250": f"s250_{lang.value}",
        }
        for lang in non_english
    })

    with patch("src.translation.translator.call_gemini_translation", return_value=mock_response) as mock_api:
        result = translate_brief_batch(sample_brief, ALL_TARGET_LANGUAGES)

    # Only ONE API call made regardless of number of languages
    mock_api.assert_called_once()
    assert len(result) == len(ALL_TARGET_LANGUAGES)


def test_batch_translation_ids_and_brief_id(sample_brief):
    non_english = [Language.ODIA, Language.HINDI, Language.ARABIC]
    mock_response = json.dumps({
        lang.value: {"title": "t", "summary_30": "s", "summary_111": "m", "summary_250": "l"}
        for lang in non_english
    })
    with patch("src.translation.translator.call_gemini_translation", return_value=mock_response):
        result = translate_brief_batch(sample_brief, non_english)

    for lang, translation in result.items():
        assert translation.brief_id == sample_brief.id
        assert translation.language == lang
        assert translation.id == f"trans_{sample_brief.id}_{lang.value}"


@pytest.mark.parametrize("lang", ALL_TARGET_LANGUAGES)
def test_each_language_produces_translation_object(sample_brief, lang):
    if lang == Language.ENGLISH:
        result = translate_brief_batch(sample_brief, [lang])
        assert isinstance(result[lang], Translation)
        return

    mock_response = json.dumps({
        lang.value: {"title": "t", "summary_30": "s", "summary_111": "m", "summary_250": "l"}
    })
    with patch("src.translation.translator.call_gemini_translation", return_value=mock_response):
        result = translate_brief_batch(sample_brief, [lang])

    assert lang in result
    assert isinstance(result[lang], Translation)
