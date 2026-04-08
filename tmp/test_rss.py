import asyncio
import httpx
from services.news_fetcher import _fetch_rss_news

async def test_rss_dates():
    async with httpx.AsyncClient(timeout=20) as client:
        # Fetch RSS news (limit 5 to be quick)
        articles = await _fetch_rss_news(client, query="", limit=5)
        
        print(f"Fetched {len(articles)} RSS articles.\n")
        for i, a in enumerate(articles):
            print(f"Article {i+1}:")
            print(f"  Title: {a['title'][:50]}...")
            print(f"  Source: {a['source']}")
            print(f"  Published At: {a['published_at']}")
            print("-" * 20)

if __name__ == "__main__":
    asyncio.run(test_rss_dates())
