"""
News Router — fetch aggregated, sentiment-tagged news from multiple APIs.
"""

from fastapi import APIRouter, Query

from services.news_fetcher import fetch_all_news

router = APIRouter(prefix="/news", tags=["News"])


@router.get("/")
async def get_news(
    q: str = Query("", description="Search query"),
    limit: int = Query(100, ge=1, le=200, description="Max articles to return"),
):
    """
    Fetch news from all configured APIs.
    Every article is tagged with VADER sentiment (Positive / Negative / Neutral).
    Results are deduplicated and sorted newest-first.
    """
    articles = await fetch_all_news(query=q, limit=limit)

    return {
        "success": True,
        "data": articles,
        "meta": {
            "total": len(articles),
            "query": q or None,
            "limit": limit,
        },
    }
