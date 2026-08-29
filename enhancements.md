# NewsBridge Backend — Enhancement List

## 1. Fix Translation — Prompt is Hardcoded to Odia Only
**Priority: High | Effort: Small | Status: ✅ Done**

`src/translation/translator.py` — `get_translation_prompt()` always said "Translate to Odia"
regardless of the `target_language` parameter. Translation to Hindi, Kannada, Tamil, Bengali,
and Telugu was broken.

- [x] Made prompt dynamic via `LANGUAGE_DISPLAY_NAMES` dict
- [x] Added language display name map (`"or" -> "Odia"`, `"hi" -> "Hindi"`, etc.)

---

## 2. Expand Language Support to Full 11 Languages
**Priority: High | Effort: Small | Status: ✅ Done**

`src/core/schemas.py` — `Language` enum was missing 6 of the 11 target languages.

### Target Language List

| Language | Code | Status |
|---|---|---|
| English | `en` | ✅ In enum |
| Odia | `or` | ✅ In enum |
| Hindi | `hi` | ✅ In enum |
| Tamil | `ta` | ✅ In enum |
| Kannada | `kn` | ✅ In enum |
| Spanish | `es` | ✅ Added |
| Cantonese | `yue` | ✅ Added |
| Bahasa Melayu | `ms` | ✅ Added |
| Dutch | `nl` | ✅ Added |
| Turkish | `tr` | ✅ Added |
| Arabic | `ar` | ✅ Added |

- [x] Added 6 missing languages to `Language` enum in `src/core/schemas.py`
- [x] Made `src/translation/glossary.py` language-agnostic (removed Odia-specific examples)

---

## 3. Batch All 11 Languages in One API Call
**Priority: Medium | Effort: Medium | Status: ✅ Done**

Previously `translate_brief()` called Gemini once per language — 11 API calls per article.

- [x] Added `translate_brief_batch(brief, target_languages)` — one Gemini call for all languages
- [x] Added `translate_briefs_batch(briefs, target_languages)` — batch across multiple briefs
- [x] English handled as pass-through (no API call, copies from Brief directly)
- [x] Returns `dict[Language, Translation]` per brief
- [x] Reduces 11 API calls -> 1 per article (~91% fewer API calls)

---

## 4. Database Retention — Rolling 7-Day Cleanup Job
**Priority: Medium | Effort: Small | Status: ✅ Done**

- [x] Standalone script: `scripts/retention_cleanup.py`
- [x] Deletes in foreign-key order: `publication_stories` -> `publications` -> `translations` -> `briefs` -> `articles`
- [x] Supports `--dry-run` and `--days N` flags
- [x] GitHub Actions cron: `.github/workflows/retention-cleanup.yml` — runs daily at 02:00 UTC
- [x] Manual trigger available from GitHub Actions UI with dry-run option

```sql
DELETE FROM translations WHERE article_id IN (
    SELECT id FROM articles WHERE published_at < NOW() - INTERVAL '7 days'
);
DELETE FROM briefs WHERE article_id IN (
    SELECT id FROM articles WHERE published_at < NOW() - INTERVAL '7 days'
);
DELETE FROM articles WHERE published_at < NOW() - INTERVAL '7 days';
```

---

## 5. Verify Gemini Free Tier / Non-Thinking Mode
**Priority: Low | Effort: Tiny | Status: Open**

At 100 articles/day the free tier (1,500 req/day) should cover costs entirely.
Non-thinking mode is the cheapest paid option if the free tier is exceeded.

- [ ] Confirm `GEMINI_TRANSLATION_MODEL` is set to `gemini-2.5-flash`
- [ ] Confirm thinking mode is not enabled in `GenerationConfig`
- [ ] Verify API key is from Google AI Studio (free tier) not Vertex AI (paid only)

---

## Summary

| # | Enhancement | Priority | Effort | Status |
|---|---|---|---|---|
| 1 | Fix hardcoded Odia prompt | High | Small | Done |
| 2 | Add 6 missing languages to enum | High | Small | Done |
| 3 | Batch 11 languages in 1 API call | Medium | Medium | Done |
| 4 | 7-day database retention cleanup | Medium | Small | Done |
| 5 | Verify Gemini free tier / non-thinking mode | Low | Tiny | Open |
