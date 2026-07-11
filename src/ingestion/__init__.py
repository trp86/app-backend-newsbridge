"""Ingestion module - RSS collection, parsing, and deduplication."""

from src.ingestion.deduplication import is_duplicate
from src.ingestion.feed_parser import parse_feed_entry
from src.ingestion.rss_collector import collect_articles

__all__ = [
    "collect_articles",
    "parse_feed_entry",
    "is_duplicate",
]
