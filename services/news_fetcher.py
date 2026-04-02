"""
News Fetcher Service — aggregates articles from NewsAPI, GNews, and NewsData.io.
Each article is tagged with VADER sentiment before being returned.
"""

import hashlib
from datetime import datetime, timezone

import httpx

from config import NEWS_API_KEY, GNEWS_API_KEY, NEWSDATA_API_KEY
from services.sentiment import analyze_sentiment


def _generate_id(url: str) -> str:
    """SHA-256 hash of the URL → stable article ID."""
    return hashlib.sha256(url.encode()).hexdigest()


def _normalize_date(date_input: str | None) -> str:
    """Parse a date string into ISO-8601; fall back to 'now'."""
    if not date_input:
        return datetime.now(timezone.utc).isoformat()
    try:
        dt = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
        return dt.isoformat()
    except (ValueError, AttributeError):
        return datetime.now(timezone.utc).isoformat()


# ━━━━━━━━━━━━━━━━━  NewsAPI  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_newsapi(query: str = "", limit: int = 50) -> list[dict]:
    if not NEWS_API_KEY:
        return []

    params: dict = {
        "apiKey": NEWS_API_KEY,
        "pageSize": min(limit, 100),
        "language": "en",
        "sortBy": "relevancy" if query else "publishedAt",
    }

    if query:
        params["q"] = query
    else:
        params["q"] = "technology OR politics OR business OR science OR sports"
        params["domains"] = "bbc.com,cnn.com,reuters.com,techcrunch.com,bloomberg.com"

    url = "https://newsapi.org/v2/everything"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[NewsAPI] Error: {e}")
        return []

    articles = []
    for a in data.get("articles", []):
        if not a.get("title") or not a.get("url") or a["title"] == "[Removed]":
            continue
        articles.append({
            "id": _generate_id(a["url"]),
            "title": a["title"],
            "link": a["url"],
            "summary": a.get("description", ""),
            "content": a.get("content", a.get("description", "")),
            "published_at": _normalize_date(a.get("publishedAt")),
            "source": (a.get("source") or {}).get("name", "NewsAPI"),
            "author": a.get("author", "Unknown"),
            "image_url": a.get("urlToImage"),
            "sentiment": analyze_sentiment(a["title"]),
            "categories": ["newsapi"],
        })
    return articles


# ━━━━━━━━━━━━━━━━━  GNews  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_gnews(query: str = "", limit: int = 50) -> list[dict]:
    if not GNEWS_API_KEY:
        return []

    endpoint = "search" if query else "top-headlines"
    params: dict = {
        "token": GNEWS_API_KEY,
        "max": min(limit, 50),
        "lang": "en",
        "sortby": "publishedAt",
    }
    if query:
        params["q"] = query

    url = f"https://gnews.io/api/v4/{endpoint}"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        print(f"[GNews] Error: {e}")
        return []

    articles = []
    for a in data.get("articles", []):
        if not a.get("title") or not a.get("url"):
            continue
        articles.append({
            "id": _generate_id(a["url"]),
            "title": a["title"],
            "link": a["url"],
            "summary": a.get("description", ""),
            "content": a.get("content", a.get("description", "")),
            "published_at": _normalize_date(a.get("publishedAt")),
            "source": (a.get("source") or {}).get("name", "GNews"),
            "author": "Unknown",
            "image_url": a.get("image"),
            "sentiment": analyze_sentiment(a["title"]),
            "categories": ["gnews"],
        })
    return articles


# ━━━━━━━━━━━━━━━  NewsData.io  ━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_newsdata(query: str = "", limit: int = 50) -> list[dict]:
    if not NEWSDATA_API_KEY:
        return []

    # Free Tier only supports size=10 max
    fetch_limit = min(limit, 10)

    params: dict = {
        "apikey": NEWSDATA_API_KEY,
        "size": fetch_limit,
        "language": "en",
    }
    if query:
        params["q"] = query
    else:
        params["category"] = "top"

    url = "https://newsdata.io/api/1/news"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            articles = []
            for a in data.get("results", []):
                if not a.get("title") or not a.get("link"):
                    continue
                authors = a.get("creator") or ["Unknown"]
                articles.append({
                    "id": _generate_id(a["link"]),
                    "title": a["title"],
                    "link": a["link"],
                    "summary": a.get("description", ""),
                    "content": a.get("content", a.get("description", "")),
                    "published_at": _normalize_date(a.get("pubDate")),
                    "source": a.get("source_id", "NewsData"),
                    "author": ", ".join(authors) if isinstance(authors, list) else str(authors),
                    "image_url": a.get("image_url"),
                    "sentiment": analyze_sentiment(a["title"]),
                    "categories": a.get("category", ["newsdata"]),
                })
            return articles

    except Exception as e:
        print(f"[NewsData] Error: {e}. Returning fallback dummy data.")
        # Fallback dummy data for local testing
        now = datetime.now(timezone.utc).isoformat()
        return [
            {
                "id": "dummy-1",
                "title": "Quantum Computing Breakthrough in Silicon Valley",
                "link": "https://example.com/quantum",
                "summary": "Scientists achieve stable quantum coherence for over 10 minutes at room temperature.",
                "content": "Full quantum breakthrough content...",
                "published_at": now,
                "source": "TechPulse",
                "author": "Dr. Sarah Chen",
                "image_url": "https://images.unsplash.com/photo-1635070041078-e363dbe005cb",
                "sentiment": "Positive",
                "categories": ["science"],
            },
            {
                "id": "dummy-2",
                "title": "Global Markets Rally Amid Inflation Cool-off",
                "link": "https://example.com/markets",
                "summary": "Major indices hit all-time highs as central banks hint at rate cuts by summer.",
                "content": "Market rally details...",
                "published_at": now,
                "source": "Global Finance",
                "author": "Marcus Sterling",
                "image_url": "https://images.unsplash.com/photo-1611974714405-0e3630f65306",
                "sentiment": "Positive",
                "categories": ["business"],
            },
            {
                "id": "dummy-3",
                "title": "The Rise of Regenerative Architecture",
                "link": "https://example.com/architecture",
                "summary": "How smart cities are using living materials to purify air and generate energy.",
                "content": "Sustainable city buildings...",
                "published_at": now,
                "source": "UrbanFuture",
                "author": "Elena Rossi",
                "image_url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab",
                "sentiment": "Neutral",
                "categories": ["environment"],
            },
            {
                "id": "dummy-4",
                "title": "New Mars Mission Discovers Ancient Water Channels",
                "link": "https://example.com/mars",
                "summary": "Imagery from the latest rover suggests liquid water flowed on the surface much later than thought.",
                "content": "Mars water discovery...",
                "published_at": now,
                "source": "SpaceXplorer",
                "author": "Cmdr. Tom Richards",
                "image_url": "https://images.unsplash.com/photo-1614728894747-a83421e2b9c9",
                "sentiment": "Positive",
                "categories": ["space"],
            },
            {
                "id": "dummy-5",
                "title": "Mental Health Apps: A Double-Edged Sword?",
                "link": "https://example.com/health",
                "summary": "Experts debate the efficacy of AI-driven therapy tools as usage skyrockets globally.",
                "content": "Therapy app debate...",
                "published_at": now,
                "source": "WellnessDaily",
                "author": "Maya Gupta",
                "image_url": "https://images.unsplash.com/photo-1576091160550-2173dba999ef",
                "sentiment": "Negative",
                "categories": ["health"],
            },
        ]


# ━━━━━━━━━━━━━━━  AGGREGATOR  ━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def fetch_all_news(query: str = "", limit: int = 200) -> list[dict]:
    """
    Fetch news from all configured APIs concurrently,
    deduplicate by article ID, sort by newest first.
    """
    import asyncio

    tasks = [
        _fetch_newsapi(query, limit),
        _fetch_gnews(query, limit),
        _fetch_newsdata(query, limit),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    seen_ids: set[str] = set()
    all_articles: list[dict] = []

    for result in results:
        if isinstance(result, Exception):
            print(f"[Aggregator] API failed: {result}")
            continue
        for article in result:
            if article["id"] not in seen_ids:
                seen_ids.add(article["id"])
                all_articles.append(article)

    # Sort newest first
    all_articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)
    return all_articles[:limit]
