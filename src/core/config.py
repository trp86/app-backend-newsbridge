"""Configuration management using Pydantic settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.schemas import RSSSource


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Google Gemini API
    gemini_api_key: str = Field(description="Google Gemini API key")
    gemini_summarization_model: str = Field(
        default="gemini-2.5-flash",
        description="Model for summarization",
    )
    gemini_translation_model: str = Field(
        default="gemini-2.5-flash",
        description="Model for translation",
    )

    # Telegram
    telegram_bot_token: str = Field(description="Telegram bot token from BotFather")
    telegram_channel_id: str = Field(description="Telegram channel ID (e.g., @channelname)")

    # Database
    database_url: str = Field(
        default="",
        description="Database URL (Neon Postgres or SQLite). Example: postgresql://user:pass@host/db",
    )
    database_path: Path = Field(
        default=Path("data/brief.db"),
        description="SQLite database path (fallback if database_url not set)",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format: json or console")

    # Scheduling
    daily_publish_time: str = Field(
        default="06:00",
        description="Daily publish time (UTC, HH:MM format)",
    )

    # Retry settings
    max_retries_per_model: int = Field(default=2, description="Max retries per model")
    request_timeout_seconds: int = Field(default=30, description="API request timeout")

    # Content filtering
    min_quality_score: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum quality score for stories",
    )
    top_stories_count: int = Field(default=5, description="Number of stories per brief")


def get_rss_sources() -> list[RSSSource]:
    """Get configured RSS sources — 11 countries (Japan, Korea, Germany, Poland,
    Bangladesh, Brazil, Mexico, Qatar, Turkey, Vietnam, China).

    Native-language sources (German, Japanese) are transformed to English during
    summarization. All other sources publish in English directly.

    Returns:
        List of RSS source configurations
    """
    return [
        # Germany
        RSSSource(name="Tagesschau", url="https://www.tagesschau.de/xml/rss2/", country="DE", priority=1, expected_articles=30),
        RSSSource(name="Süddeutsche Zeitung", url="https://www.sueddeutsche.de/news/rss", country="DE", priority=1, expected_articles=25),
        RSSSource(name="Der Spiegel International", url="https://www.spiegel.de/international/index.rss", country="DE", priority=1, expected_articles=15),
        RSSSource(name="Deutsche Welle World", url="https://rss.dw.com/xml/rss-en-world", country="DE", priority=1, expected_articles=25),
        RSSSource(name="Handelsblatt Global", url="https://www.handelsblatt.com/contentexport/feed/top-themen", country="DE", priority=1, expected_articles=20),
        # Japan
        RSSSource(name="NHK News", url="https://www3.nhk.or.jp/rss/news/cat0.xml", country="JP", priority=1, expected_articles=30),
        RSSSource(name="NHK World", url="https://www3.nhk.or.jp/nhkworld/en/news/feeds/", country="JP", priority=1, expected_articles=20),
        RSSSource(name="Japan Times", url="https://www.japantimes.co.jp/feed/", country="JP", priority=1, expected_articles=20),
        RSSSource(name="Nikkei Asia", url="https://asia.nikkei.com/rss/feed/nar", country="JP", priority=2, expected_articles=15),
        # Korea
        RSSSource(name="KBS News", url="https://news.kbs.co.kr/rss/rss.htm", country="KR", priority=1, expected_articles=25),
        RSSSource(name="Yonhap News", url="https://en.yna.co.kr/RSS/news.xml", country="KR", priority=2, expected_articles=25),
        RSSSource(name="Korea Herald", url="https://www.koreaherald.com/common/rss_xml.php", country="KR", priority=2, expected_articles=20),
        # Poland
        RSSSource(name="TVN24", url="https://tvn24.pl/najnowsze.xml", country="PL", priority=1, expected_articles=20),
        RSSSource(name="Notes from Poland", url="https://notesfrompoland.com/feed/", country="PL", priority=2, expected_articles=15),
        RSSSource(name="Polish Radio EN", url="https://www.polskieradio.pl/395/feed", country="PL", priority=2, expected_articles=15),
        # Bangladesh
        RSSSource(name="Prothom Alo", url="https://www.prothomalo.com/feed", country="BD", priority=1, expected_articles=20),
        RSSSource(name="The Daily Star BD", url="https://www.thedailystar.net/rss.xml", country="BD", priority=2, expected_articles=20),
        RSSSource(name="Dhaka Tribune", url="https://www.dhakatribune.com/feed", country="BD", priority=2, expected_articles=20),
        # Brazil
        RSSSource(name="G1 Globo", url="https://g1.globo.com/rss/g1/", country="BR", priority=1, expected_articles=25),
        RSSSource(name="Agência Brasil EN", url="https://agenciabrasil.ebc.com.br/en/rss/feed", country="BR", priority=2, expected_articles=20),
        RSSSource(name="The Rio Times", url="https://riotimesonline.com/feed/", country="BR", priority=2, expected_articles=15),
        # Mexico
        RSSSource(name="El Universal", url="https://www.eluniversal.com.mx/rss.xml", country="MX", priority=1, expected_articles=20),
        RSSSource(name="Mexico News Daily", url="https://mexiconewsdaily.com/feed/", country="MX", priority=2, expected_articles=20),
        # Qatar
        RSSSource(name="Al Jazeera Arabic", url="https://www.aljazeera.net/aljazeerarss/a2zfeeds/a2z_xml_news_ar.xml", country="QA", priority=1, expected_articles=25),
        RSSSource(name="Al Jazeera English", url="https://www.aljazeera.com/xml/rss/all.xml", country="QA", priority=2, expected_articles=30),
        RSSSource(name="Gulf Times", url="https://www.gulf-times.com/rss/recent", country="QA", priority=2, expected_articles=15),
        # Turkey
        RSSSource(name="Hürriyet", url="https://www.hurriyet.com.tr/rss/anasayfa", country="TR", priority=1, expected_articles=25),
        RSSSource(name="NTV Haber", url="https://www.ntv.com.tr/gundem.rss", country="TR", priority=1, expected_articles=20),
        RSSSource(name="Daily Sabah", url="https://www.dailysabah.com/rss", country="TR", priority=2, expected_articles=20),
        RSSSource(name="TRT World", url="https://www.trtworld.com/rss", country="TR", priority=2, expected_articles=20),
        # Vietnam
        RSSSource(name="VnExpress", url="https://vnexpress.net/rss/tin-moi-nhat.rss", country="VN", priority=1, expected_articles=25),
        RSSSource(name="VnExpress International", url="https://e.vnexpress.net/rss/news.rss", country="VN", priority=2, expected_articles=20),
        RSSSource(name="Tuoi Tre News", url="https://tuoitrenews.vn/rss/latest.rss", country="VN", priority=2, expected_articles=15),
        # China
        RSSSource(name="Xinhua", url="https://www.xinhuanet.com/rss/news.xml", country="CN", priority=1, expected_articles=25),
        RSSSource(name="People's Daily", url="https://www.people.com.cn/rss/politics.xml", country="CN", priority=1, expected_articles=20),
        RSSSource(name="China Daily", url="https://www.chinadaily.com.cn/rss/world_rss.xml", country="CN", priority=2, expected_articles=20),
        RSSSource(name="Global Times", url="https://www.globaltimes.cn/rss/outbrain.xml", country="CN", priority=2, expected_articles=15),
    ]


@lru_cache
def get_source_priority_map() -> dict[str, int]:
    """Return a mapping of source name → priority (1=native, 2=English edition)."""
    return {source.name: source.priority for source in get_rss_sources()}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings instance loaded from environment
    """
    return Settings()
