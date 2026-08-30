"""Prompts for meaningful summarization and transformation."""

# Maps source name → content language code.
# Sources not listed here are assumed to publish in English.
SOURCE_LANGUAGE: dict[str, str] = {
    # Germany
    "Tagesschau": "de",
    "Süddeutsche Zeitung": "de",
    # Japan
    "NHK News": "ja",
    # Turkey
    "Hürriyet": "tr",
    "NTV Haber": "tr",
    # Korea
    "KBS News": "ko",
    # Poland
    "TVN24": "pl",
    # Bangladesh
    "Prothom Alo": "bn",
    # Brazil
    "G1 Globo": "pt",
    # Mexico
    "El Universal": "es",
    # Qatar
    "Al Jazeera Arabic": "ar",
    # Vietnam
    "VnExpress": "vi",
    # China
    "Xinhua": "zh",
    "People's Daily": "zh",
}

# Language code → (display name, key terms, country context)
_LANG_META: dict[str, tuple[str, str, str]] = {
    "de": (
        "German",
        "Bundeskanzler = Chancellor (Germany's head of government), Bundestag = Federal Parliament",
        "Germany = Europe's largest economy, founding EU member, key NATO ally",
    ),
    "ja": (
        "Japanese",
        "首相 (Shushō) = Prime Minister, 国会 (Kokkai) = National Diet (parliament)",
        "Japan = world's 4th largest economy, key US ally in Asia, pacifist constitution",
    ),
    "tr": (
        "Turkish",
        "Cumhurbaşkanı = President, Büyük Millet Meclisi = Grand National Assembly",
        "Turkey = NATO member bridging Europe and Asia, major regional power, G20 economy",
    ),
    "ko": (
        "Korean",
        "대통령 (Daetongnyeong) = President, 국회 (Gukhoe) = National Assembly",
        "South Korea = world's 13th largest economy, divided peninsula, major tech exporter (Samsung, Hyundai)",
    ),
    "pl": (
        "Polish",
        "Prezydent = President, Sejm = lower house of parliament, Senat = upper house",
        "Poland = EU and NATO member, largest economy in Central Europe, key eastern flank ally",
    ),
    "bn": (
        "Bengali",
        "রাষ্ট্রপতি (Rashtropati) = President, প্রধানমন্ত্রী (Pradhanmantri) = Prime Minister",
        "Bangladesh = 8th most populous country, world's largest garment exporter, fast-growing economy",
    ),
    "pt": (
        "Brazilian Portuguese",
        "Presidente = President, Câmara dos Deputados = Chamber of Deputies (lower house)",
        "Brazil = world's 9th largest economy, Amazon rainforest steward, BRICS member",
    ),
    "es": (
        "Spanish",
        "Presidente = President, Congreso = Congress, Senado = Senate",
        "Mexico = 2nd largest economy in Latin America, shares world's busiest border with the US, USMCA member",
    ),
    "ar": (
        "Arabic",
        "رئيس الوزراء = Prime Minister, أمير = Emir, مجلس الشورى = Shura Council",
        "Qatar = world's largest LNG exporter, hosts US military base, 2022 FIFA World Cup host; note: Arabic is read right-to-left",
    ),
    "vi": (
        "Vietnamese",
        "Tổng Bí thư = General Secretary (most powerful role), Thủ tướng = Prime Minister",
        "Vietnam = one-party communist state, one of Southeast Asia's fastest-growing economies, major manufacturing hub",
    ),
    "zh": (
        "Chinese (Simplified)",
        "总书记 (Zǒng Shūjì) = General Secretary (most powerful role), 总理 (Zǒnglǐ) = Premier",
        "China = world's 2nd largest economy, permanent UN Security Council member, central to US-China geopolitical rivalry",
    ),
}


def _native_to_english_prompt(title: str, content: str, lang_code: str) -> str:
    """Build a native-language → English transformation prompt."""
    lang_name, terms, context = _LANG_META[lang_code]
    return f"""You are a news editor transforming {lang_name} news for international readers.

Read this {lang_name} article and create 3 English summaries that are clear and understandable for people who don't follow this country's politics or culture.

Don't just translate - EXPLAIN. Add context. Answer "Why should I care?"

{lang_name.upper()} ARTICLE:
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
- Add context for international readers
- Why this is globally significant

3. DEEP DIVE (exactly 250 words):
- Full story with background
- What happened, why it matters, what's next
- Explain political/cultural context
- Global implications
- Key stakeholders and their positions

IMPORTANT:
- Explain local terms ({terms})
- Add context ({context})
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


def get_summarization_prompt(article_title: str, article_content: str, source_name: str) -> str:
    """Get appropriate summarization prompt based on source language."""
    lang = SOURCE_LANGUAGE.get(source_name, "en")
    if lang == "en":
        return get_english_summarization_prompt(article_title, article_content)
    return _native_to_english_prompt(article_title, article_content, lang)


# Keep named wrappers for backwards compatibility and direct use in tests
def get_german_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "de")


def get_japanese_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "ja")


def get_turkish_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "tr")


def get_korean_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "ko")


def get_polish_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "pl")


def get_bengali_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "bn")


def get_portuguese_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "pt")


def get_spanish_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "es")


def get_arabic_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "ar")


def get_vietnamese_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "vi")


def get_chinese_transformation_prompt(title: str, content: str) -> str:
    return _native_to_english_prompt(title, content, "zh")


def get_english_summarization_prompt(title: str, content: str) -> str:
    """Prompt for English → English summarization."""
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
