"""Prompts for meaningful summarization and transformation."""

# German sources that need meaningful transformation to English
GERMAN_SOURCES = {"Tagesschau", "Süddeutsche Zeitung"}


def get_summarization_prompt(article_title: str, article_content: str, source_name: str) -> str:
    """Get appropriate summarization prompt based on source language.

    Args:
        article_title: Article title
        article_content: Article content
        source_name: Source name (to detect language)

    Returns:
        Formatted prompt for LLM
    """
    is_german = source_name in GERMAN_SOURCES

    if is_german:
        return get_german_transformation_prompt(article_title, article_content)
    else:
        return get_english_summarization_prompt(article_title, article_content)


def get_german_transformation_prompt(title: str, content: str) -> str:
    """Prompt for German → English meaningful transformation.

    Not literal translation - explain meaningfully for international readers.
    """
    return f"""You are a news editor transforming German news for international readers.

Read this German article and create 3 English summaries that are clear and understandable for people who don't follow German politics or culture.

Don't just translate - EXPLAIN. Add context. Answer "Why should I care?"

GERMAN ARTICLE:
Title: {title}
Content: {content}

Create exactly 3 summaries in English:

1. HEADLINE (exactly 30 words):
- What happened in one sentence
- Clear and complete
- No clickbait

2. BRIEF (exactly 111 words):
- What happened and why it matters
- Who's involved (explain roles/positions)
- Add context for non-German readers
- Why this is globally significant

3. DEEP DIVE (exactly 250 words):
- Full story with background
- What happened, why it matters, what's next
- Explain German political/cultural context
- Global implications
- Key stakeholders and their positions

IMPORTANT:
- Explain German terms (Bundeskanzler = Chancellor, Germany's leader)
- Add context (Germany = Europe's largest economy)
- Make it meaningful, not literal translation
- Write naturally in English
- Stick to exact word counts

CRITICAL: Return ONLY valid JSON. No markdown, no explanation, no extra text.
Start your response with {{ and end with }}

Format:
{{
  "summary_30": "your 30-word summary here",
  "summary_111": "your 111-word summary here",
  "summary_250": "your 250-word summary here"
}}"""


def get_english_summarization_prompt(title: str, content: str) -> str:
    """Prompt for English → English summarization.

    Standard summarization with word count constraints.
    """
    return f"""You are a news editor creating a daily knowledge brief.

Summarize this article in 3 different lengths. Focus on clarity and completeness.

ARTICLE:
Title: {title}
Content: {content}

Create exactly 3 summaries:

1. HEADLINE (exactly 30 words):
- What happened in one sentence
- Clear and direct
- Complete thought

2. BRIEF (exactly 111 words):
- What happened
- Why it matters
- Who's involved
- Key context

3. DEEP DIVE (exactly 250 words):
- Full story with details
- What happened, why it matters, what happens next
- Background and context
- Implications and significance
- Key quotes or data points

RULES:
- Stick to exact word counts (30, 111, 250)
- Neutral tone (no sensationalism)
- Focus on facts
- Answer: What? Why? So what?

CRITICAL: Return ONLY valid JSON. No markdown, no explanation, no extra text.
Start your response with {{ and end with }}

Format:
{{
  "summary_30": "your 30-word summary here",
  "summary_111": "your 111-word summary here",
  "summary_250": "your 250-word summary here"
}}"""


# Validation prompt to check if summaries meet requirements
VALIDATION_PROMPT = """Check if these summaries meet the requirements:

1. Word counts: 30, 111, 250 (±5 words tolerance)
2. Complete sentences (no cut-offs)
3. Neutral tone (no clickbait)
4. Factual accuracy

Summaries:
{summaries}

Return JSON:
{{
  "valid": true/false,
  "issues": ["list of issues if any"]
}}"""
