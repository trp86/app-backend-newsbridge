"""Test the API endpoint directly without HTTP."""

from src.api.main import get_articles


async def main():
    """Test get_articles endpoint."""
    result = await get_articles(limit=3)
    print(f"Articles found: {len(result.articles)}")
    if result.articles:
        print(f"First article: {result.articles[0].english['title']}")
    else:
        print("No articles returned")
    print(f"Metadata: {result.metadata}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
