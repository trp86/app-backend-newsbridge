-- Global Knowledge Brief Database Schema
-- Compatible with PostgreSQL (Neon) and SQLite
-- Created: 2026-07-04

-- Raw articles from RSS feeds
CREATE TABLE IF NOT EXISTS articles (
    id TEXT PRIMARY KEY,
    source_url TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL CHECK(source_type IN ('rss', 'api')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    content_hash TEXT NOT NULL,
    is_duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- English briefs (summarized articles)
CREATE TABLE IF NOT EXISTS briefs (
    id TEXT PRIMARY KEY,
    article_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary_30 TEXT NOT NULL,
    summary_111 TEXT NOT NULL,
    summary_250 TEXT NOT NULL,
    category TEXT NOT NULL,
    quality_score NUMERIC NOT NULL CHECK(quality_score >= 0 AND quality_score <= 1),
    model_used TEXT NOT NULL,
    processed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

-- Translations (Odia, Hindi, etc.)
CREATE TABLE IF NOT EXISTS translations (
    id TEXT PRIMARY KEY,
    brief_id TEXT NOT NULL,
    language TEXT NOT NULL CHECK(language IN ('en', 'or', 'hi', 'bn', 'te', 'kn', 'ta')),
    title TEXT NOT NULL,
    summary_30 TEXT NOT NULL,
    summary_111 TEXT NOT NULL,
    summary_250 TEXT NOT NULL,
    model_used TEXT NOT NULL,
    translated_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brief_id) REFERENCES briefs(id)
);

-- Publications (daily brief metadata)
CREATE TABLE IF NOT EXISTS publications (
    id TEXT PRIMARY KEY,
    date DATE NOT NULL,
    language TEXT NOT NULL CHECK(language IN ('en', 'or', 'hi', 'bn', 'te', 'kn', 'ta')),
    telegram_message_id TEXT,
    publish_status TEXT NOT NULL CHECK(publish_status IN ('pending', 'sent', 'failed')),
    published_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, language)
);

-- Junction table for publication stories
CREATE TABLE IF NOT EXISTS publication_stories (
    publication_id TEXT NOT NULL,
    translation_id TEXT NOT NULL,
    position INTEGER NOT NULL CHECK(position >= 1 AND position <= 5),
    PRIMARY KEY (publication_id, translation_id),
    FOREIGN KEY (publication_id) REFERENCES publications(id),
    FOREIGN KEY (translation_id) REFERENCES translations(id)
);

-- API usage logs for cost tracking
CREATE TABLE IF NOT EXISTS api_logs (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,
    model_used TEXT NOT NULL,
    operation TEXT NOT NULL CHECK(operation IN ('summarize', 'translate')),
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd NUMERIC,
    latency_ms INTEGER,
    success BOOLEAN NOT NULL,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_articles_published ON articles(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_hash ON articles(content_hash);
CREATE INDEX IF NOT EXISTS idx_articles_duplicate ON articles(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_briefs_article ON briefs(article_id);
CREATE INDEX IF NOT EXISTS idx_briefs_quality ON briefs(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_translations_brief ON translations(brief_id);
CREATE INDEX IF NOT EXISTS idx_translations_language ON translations(language);
CREATE INDEX IF NOT EXISTS idx_publications_date ON publications(date DESC);
CREATE INDEX IF NOT EXISTS idx_publications_status ON publications(publish_status);
CREATE INDEX IF NOT EXISTS idx_api_logs_timestamp ON api_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_api_logs_operation ON api_logs(operation);
