"""Combined prompt for summarization + translation in one API call."""

from src.core.schemas import Language, RawArticle
from src.translation.glossary import get_glossary_instructions


def get_combined_prompt(article: RawArticle, target_language: Language = Language.ODIA) -> str:
    """Generate combined prompt for summarization + translation in one call.

    This prompt asks the LLM to:
    1. Summarize the article in English (30/111/250 words)
    2. Translate those summaries to target language (Odia)

    All in ONE API call, returning structured JSON.

    Args:
        article: Raw article to process
        target_language: Target language for translation (default: Odia)

    Returns:
        Formatted prompt for combined processing
    """
    glossary = get_glossary_instructions()

    # Determine if this is a German source
    german_sources = {"Tagesschau", "Süddeutsche Zeitung"}
    is_german = article.source_name in german_sources

    if is_german:
        summarization_instructions = """
STEP 1: TRANSFORM TO ENGLISH (Meaningful, not literal)

This is a German news article. Your job is to TRANSFORM it into meaningful English.

IMPORTANT:
- DON'T just translate word-for-word
- EXPLAIN what's happening for international readers
- ADD context (e.g., "Germany = Europe's largest economy")
- Make it understandable for someone who doesn't know German politics/culture
- Keep it factual and journalistic

Example:
❌ BAD: "The Bundestag voted on the law"
✅ GOOD: "Germany's parliament (Bundestag) voted on the law"
"""
    else:
        summarization_instructions = """
STEP 1: SUMMARIZE IN ENGLISH

This is an English news article. Summarize it clearly and concisely.

IMPORTANT:
- Keep the key facts and context
- Maintain neutral, journalistic tone
- Focus on what happened, why it matters
- No clickbait or sensationalism
"""

    return f"""You are a professional news editor and translator.

TASK: Process this news article in TWO STEPS (in ONE response):

{summarization_instructions}

Create THREE summaries:
- 30 words: Headline-style, captures the essence
- 111 words: Short brief with key details
- 250 words: Full brief with context and implications

---

STEP 2: TRANSLATE TO {target_language.value.upper()}

Take the English summaries from Step 1 and translate them to {target_language.value}.

{glossary}

---

ARTICLE TO PROCESS:

Source: {article.source_name}
Title: {article.title}
Content: {article.content}

---

CRITICAL: Return ONLY valid JSON. No markdown, no explanation, no extra text.
Start your response with {{ and end with }}

Format:
{{
  "english_title": "concise English title (~10 words)",
  "english_30": "30-word English summary",
  "english_111": "111-word English summary",
  "english_250": "250-word English summary",
  "odia_title": "translated title in Odia",
  "odia_30": "30-word summary in Odia",
  "odia_111": "111-word summary in Odia",
  "odia_250": "250-word summary in Odia"
}}

Remember:
- STEP 1: Create English summaries (meaningful transformation for German, standard for English)
- STEP 2: Translate those summaries to {target_language.value}
- Return ALL 8 fields in ONE JSON response
"""
