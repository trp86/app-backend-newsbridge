"""Technical glossary - terms to keep in English or transliterate."""

# Proper nouns - keep in English/original language
PROPER_NOUNS = {
    # Countries
    "Germany",
    "United States",
    "USA",
    "Russia",
    "Ukraine",
    "Morocco",
    "Canada",
    "Egypt",
    "Argentina",
    # Organizations
    "NATO",
    "UN",
    "EU",
    "European Union",
    "AfD",
    "NASA",
    "WHO",
    # Companies
    "Condor",
    "Google",
    "Microsoft",
    "Apple",
    "Tesla",
    # People (titles can be translated)
    "Trump",
    "Biden",
    "Putin",
    "Zelenskyy",
    "Selenskyj",
    "Chrupalla",
    "Nagelsmann",
    "Klopp",
}

# Technical terms - keep in English with Odia explanation if needed
TECHNICAL_TERMS = {
    "GDP",
    "API",
    "AI",
    "CEO",
    "COVID-19",
    "NATO",
    "IMF",
    "World Bank",
}

# Sports terms - can be transliterated
SPORTS_TERMS = {
    "World Cup",
    "FIFA",
    "Olympics",
    "Champions League",
}


def get_glossary_instructions() -> str:
    """Get instructions for handling special terms in translation.

    Returns:
        Instructions text for LLM prompt
    """
    return """
GLOSSARY RULES:

1. Keep these in ENGLISH (do NOT translate):
   - Country names: Germany, United States, Russia, etc.
   - Company names: Condor, Google, Tesla, etc.
   - Person names: Trump, Putin, Chrupalla, etc.
   - Acronyms: NASA, EU, NATO, GDP, CEO, etc.

2. Translate these naturally into the target language:
   - Titles: "President", "Chancellor", "Minister"
   - Common nouns: "airline", "government", "economy"
   - Verbs and adjectives: translate naturally

3. Cultural adaptation:
   - Do NOT translate word-for-word
   - Use natural phrasing appropriate for native readers of the target language
   - Keep the meaning and journalistic tone
   - For right-to-left languages (Arabic): ensure correct directionality

Examples:
- "German Chancellor Olaf Scholz" → keep "Olaf Scholz" and "Germany", translate the title
- "NASA announced" → keep "NASA", translate the verb
- "the airline Condor" → keep "Condor", translate "airline"
"""
