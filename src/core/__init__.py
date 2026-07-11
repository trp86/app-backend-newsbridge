"""Core module - configuration, schemas, database, logging."""

from src.core.config import get_settings
from src.core.database import get_db_connection, init_database
from src.core.logging import setup_logging
from src.core.schemas import (
    APICallLog,
    Brief,
    DailyBrief,
    Language,
    RawArticle,
    SourceType,
    Translation,
)

__all__ = [
    "get_settings",
    "get_db_connection",
    "init_database",
    "setup_logging",
    "APICallLog",
    "Brief",
    "DailyBrief",
    "Language",
    "RawArticle",
    "SourceType",
    "Translation",
]
