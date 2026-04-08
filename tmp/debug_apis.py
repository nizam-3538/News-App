import asyncio
import httpx
from services.news_fetcher import _fetch_newsapi, _fetch_gnews, _fetch_newsdata, _fetch_rss_news
from config import NEWS_API_KEY, GNEWS_API_KEY, NEWSDATA_API_KEY

async def debug_apis():
    print(f"DEBUG: NEWS_API_KEY={NEWS_API_KEY[:5]}...")
    print(f"DEBUG: GNEWS_API_KEY={GNEWS_API_KEY[:5]}...")
    print(f"DEBUG: NEWSDATA_API_KEY={NEWSDATA_API_KEY[:5]}...")

    async with httpx.AsyncClient(timeout=20) as client:
        print("\nTesting NewsAPI...")
        newsapi = await _fetch_newsapi(client, limit=5)
        print(f"NewsAPI returned {len(newsapi)} articles.")
        if newsapi:
            print(f"Sample source from NewsAPI: {newsapi[0]['source']}")

        print("\nTesting GNews...")
        gnews = await _fetch_gnews(client, limit=5)
        print(f"GNews returned {len(gnews)} articles.")
        if gnews:
            print(f"Sample source from GNews: {gnews[0]['source']}")

        print("\nTesting NewsData...")
        newsdata = await _fetch_newsdata(client, limit=5)
        print(f"NewsData returned {len(newsdata)} articles.")
        if newsdata:
            print(f"Sample source from NewsData: {newsdata[0]['source']}")

        print("\nTesting RSS...")
        rss = await _fetch_rss_news(client, limit=5)
        print(f"RSS returned {len(rss)} articles.")
        if rss:
            print(f"Sample source from RSS: {rss[0]['source']}")

if __name__ == "__main__":
    asyncio.run(debug_apis())
