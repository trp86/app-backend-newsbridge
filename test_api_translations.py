"""Test if translations are being loaded correctly."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.storage.translation_repository import TranslationRepository
from src.storage.brief_repository import BriefRepository

# Get first brief
briefs = BriefRepository.get_recent_briefs(limit=1)
if not briefs:
    print("No briefs found!")
    sys.exit(1)

brief = briefs[0]
print(f"Brief ID: {brief.id}")
print(f"Brief Title: {brief.title}")

# Get translations for this brief
translations = {}
brief_translations = TranslationRepository.get_translations_by_brief(brief_id=brief.id)
print(f"\nTranslations found in DB: {len(brief_translations)}")

for translation in brief_translations:
    print(f"  Language: {translation.language.value}")
    translations[translation.language.value] = {
        "title": translation.title,
        "summary_30": translation.summary_30,
        "summary_111": translation.summary_111,
        "summary_250": translation.summary_250,
    }

print(f"\nTranslations dict keys: {list(translations.keys())}")
print(f"Has Odia ('or'): {'or' in translations}")

if 'or' in translations:
    print("\nOdia translation exists!")
    print(f"Odia title length: {len(translations['or']['title'])} characters")
else:
    print("\nERROR: Odia translation not added to dict!")
