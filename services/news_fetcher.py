"""
News Fetcher Service — aggregates articles from NewsAPI, GNews, and NewsData.io.
Each article is tagged with VADER sentiment before being returned.
"""

import hashlib
import re
from datetime import datetime, timezone

import httpx
import feedparser
import asyncio
from time import mktime

from config import NEWS_API_KEY, GNEWS_API_KEY, NEWSDATA_API_KEY
from services.sentiment import analyze_sentiment

# High-quality global RSS feeds for hybrid fallback
RSS_FEEDS = [
    {"name": "BBC World", "url": "http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "NYT World", "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml"},
    {"name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "Reuters World", "url": "https://www.reutersagency.com/feed/?best-topics=world-news&post_type=best"},
]


def _generate_id(url: str) -> str:
    """SHA-256 hash of the URL → stable article ID."""
    return hashlib.sha256(url.encode()).hexdigest()


def _normalize_date(date_input: str | None) -> str | None:
    """Parse a date string into ISO-8601; fall back to None."""
    if not date_input:
        return None
    try:
        # Handle various date formats from different APIs
        # Try fromisoformat first (covers NewsAPI 'Z' format)
        dt = datetime.fromisoformat(date_input.replace("Z", "+00:00"))
        return dt.isoformat()
    except (ValueError, AttributeError):
        # Fallback for other formats like RSS (RFC 822) or GNews
        try:
            # Using feedparser's internal parsing logic for robustness
            import feedparser._parsers as parsers
            dt_tuple = parsers.parse_date(date_input)
            dt = datetime(*dt_tuple[:6], tzinfo=timezone.utc)
            return dt.isoformat()
        except Exception:
            # If all parsing fails, return None
            return None


# ━━━━━━━━━━━━━━━━━  NewsAPI  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_newsapi(client: httpx.AsyncClient, query: str = "", limit: int = 50) -> list[dict]:
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
    headers = {"User-Agent": "NewsApp/1.0 (Contact: admin@example.com)"}
    try:
        resp = await client.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"[NewsAPI] Status Error {resp.status_code}: {resp.text}")
            return []
        data = resp.json()
    except Exception as e:
        print(f"[NewsAPI] Connection Error: {e}")
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

async def _fetch_gnews(client: httpx.AsyncClient, query: str = "", limit: int = 50) -> list[dict]:
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
    headers = {"User-Agent": "NewsApp/1.0"}
    try:
        resp = await client.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"[GNews] Status Error {resp.status_code}: {resp.text}")
            return []
        data = resp.json()
    except Exception as e:
        print(f"[GNews] Connection Error: {e}")
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

async def _fetch_newsdata(client: httpx.AsyncClient, query: str = "", limit: int = 50) -> list[dict]:
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
    headers = {"User-Agent": "NewsApp/1.0"}
    try:
        resp = await client.get(url, params=params, headers=headers)
        if resp.status_code != 200:
            print(f"[NewsData] Status Error {resp.status_code}: {resp.text}")
            return []
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
                "categories": (a.get("category") or []) + ["newsdata"],
            })
        return articles

    except Exception as e:
        print(f"[NewsData] Connection Error: {e}. Returning fallback dummy data.")
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


# ━━━━━━━━━━━━━━━━━  RSS Engine  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def _fetch_rss_news(client: httpx.AsyncClient, query: str = "", limit: int = 50) -> list[dict]:
    """Fetch and parse RSS feeds concurrently using feedparser."""
    
    async def parse_single_feed(source_info: dict):
        try:
            # RSS fetching is blocking; use to_thread
            feed = await asyncio.to_thread(feedparser.parse, source_info["url"])
            articles = []
            for entry in feed.entries[:limit]:
                # Filter by query if present
                if query and query.lower() not in (entry.title + entry.get("summary", "")).lower():
                    continue

                # Strip HTML from summary
                raw_summary = entry.get("summary", entry.get("description", ""))
                clean_summary = re.sub(r'<[^>]*>', '', raw_summary).strip()

                # 🛡️ DATE EXTRACTION: Use feedparser's parsed date for consistency
                pub_date = None
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    # Convert struct_time to a standard ISO-8601 string
                    dt = datetime.fromtimestamp(mktime(entry.published_parsed), timezone.utc)
                    pub_date = dt.isoformat()
                elif hasattr(entry, 'published'):
                    # Fallback to the raw string if parsed is unavailable
                    pub_date = _normalize_date(entry.published)

                articles.append({
                    "id": _generate_id(entry.link),
                    "title": entry.title,
                    "link": entry.link,
                    "summary": clean_summary,
                    "content": clean_summary,
                    "published_at": pub_date,
                    "source": source_info["name"],
                    "author": entry.get("author", "Unknown"),
                    "image_url": entry.get("media_content", [{}])[0].get("url") if entry.get("media_content") else None,
                    "sentiment": analyze_sentiment(entry.title),
                    "categories": ["rss"],
                })
            return articles
        except Exception as e:
            print(f"[RSS] Error fetching {source_info['name']}: {e}")
            return []

    tasks = [parse_single_feed(f) for f in RSS_FEEDS]
    results = await asyncio.gather(*tasks)
    
    # Flatten list of lists
    return [item for sublist in results for item in sublist]


# ━━━━━━━━━━━━━━━  AGGREGATOR  ━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def fetch_all_news(query: str = "", limit: int = 200) -> list[dict]:
    """
    Hybrid Aggregation Engine:
    1. Fetches from NewsAPI, GNews, NewsData.io (REST).
    2. Fetches from global RSS feeds (XML).
    3. Performs two-pass deduplication (ID then Normalized Title).
    4. Reports source counts to console.
    """
    async with httpx.AsyncClient(timeout=20) as client:
        tasks = [
            _fetch_newsapi(client, query, limit),
            _fetch_gnews(client, query, limit),
            _fetch_newsdata(client, query, limit),
            _fetch_rss_news(client, query, limit),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    seen_ids: set[str] = set()
    seen_titles: set[str] = set()
    all_articles: list[dict] = []
    
    source_counts = {
        "NewsAPI": 0,
        "GNews": 0,
        "NewsData": 0,
        "RSS": 0,
        "Other": 0
    }

    for result in results:
        if isinstance(result, Exception):
            print(f"[Aggregator] Task failed: {result}")
            continue

        for article in result:
            # Pass 1: ID Deduplication
            if article["id"] in seen_ids:
                continue
            
            # Pass 2: Title-based Deduplication (Aggressive)
            # Normalize: remove non-alphanumeric and lowercase
            norm_title = re.sub(r'\W+', '', article["title"].lower())
            if norm_title in seen_titles:
                continue

            seen_ids.add(article["id"])
            seen_titles.add(norm_title)
            all_articles.append(article)

            # 🛡️ FIXED COUNTING LOGIC (Using Tags, not Names)
            tags = article.get("categories", [])
            if "rss" in tags:
                source_counts["RSS"] += 1
            elif "newsapi" in tags or "newsapi" in article.get("source", "").lower():
                source_counts["NewsAPI"] += 1
            elif "gnews" in tags or "gnews" in article.get("source", "").lower():
                source_counts["GNews"] += 1
            elif "newsdata" in tags or "newsdata" in article.get("source", "").lower():
                source_counts["NewsData"] += 1
            else:
                source_counts["Other"] += 1

    # Print Source Report
    print(f"\n[Aggregator Report] Total Unique: {len(all_articles)}")
    print(f" -> NewsAPI: {source_counts['NewsAPI']}")
    print(f" -> GNews: {source_counts['GNews']}")
    print(f" -> NewsData: {source_counts['NewsData']}")
    print(f" -> RSS Feeds: {source_counts['RSS']}")
    print(f" -> Other: {source_counts['Other']}\n")

    # Sort by image presence first, then by date. Articles without images are pushed down.
    all_articles.sort(key=lambda a: (bool(a.get("image_url")), a.get("published_at") or ""), reverse=True)
    return all_articles[:limit]
