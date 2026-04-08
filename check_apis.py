import asyncio
import httpx
from config import NEWS_API_KEY, GNEWS_API_KEY, NEWSDATA_API_KEY

async def test_apis():
    async with httpx.AsyncClient() as client:
        # Test NewsAPI
        print("Testing NewsAPI...")
        try:
            url = f"https://newsapi.org/v2/everything?q=technology&apiKey={NEWS_API_KEY}"
            resp = await client.get(url)
            print(f"NewsAPI Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"NewsAPI Error Body: {resp.text}")
        except Exception as e:
            print(f"NewsAPI Exception: {e}")

        # Test GNews
        print("\nTesting GNews...")
        try:
            url = f"https://gnews.io/api/v4/top-headlines?token={GNEWS_API_KEY}&lang=en"
            resp = await client.get(url)
            print(f"GNews Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"GNews Error Body: {resp.text}")
        except Exception as e:
            print(f"GNews Exception: {e}")

        # Test NewsData
        print("\nTesting NewsData...")
        try:
            url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}"
            resp = await client.get(url)
            print(f"NewsData Status: {resp.status_code}")
            if resp.status_code != 200:
                print(f"NewsData Error Body: {resp.text}")
        except Exception as e:
            print(f"NewsData Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_apis())
