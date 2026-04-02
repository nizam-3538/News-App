"""
Saved Articles Router — CRUD with 500-article limit per user.
Cross-device sync via MongoDB.
"""

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, HTTPException, Depends, Query

from dependencies import get_current_user
from models import SaveArticleRequest, SavedArticleOut
import database

router = APIRouter(tags=["Saved Articles"])


@router.get("/", response_model=List[SavedArticleOut])
async def list_saved_articles(
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Fetch saved articles for the current user, newest first."""
    db = database.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    cursor = (
        db.saved_articles.find({"user_id": current_user["id"]})
        .sort("saved_at", -1)
        .skip(skip)
        .limit(limit)
    )
    articles = await cursor.to_list(length=limit)
    
    # Map to output model
    return [
        SavedArticleOut(
            user_id=a["user_id"],
            article_id=a["article_id"],
            title=a["title"],
            url=a["url"],
            summary=a.get("summary"),
            source=a.get("source"),
            author=a.get("author"),
            image_url=a.get("image_url"),
            published_at=a.get("published_at"),
            sentiment=a.get("sentiment"),
            categories=a.get("categories", []),
            saved_at=a["saved_at"],
        )
        for a in articles
    ]


@router.post("/", status_code=201)
async def save_article(
    article: SaveArticleRequest,
    current_user: dict = Depends(get_current_user),
):
    """Save an article. Enforces the 500-article limit per user."""
    db = database.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # ── 500-article limit ──────────────────────────────────
    MAX_LIMIT = 500
    current_count = await db.saved_articles.count_documents(
        {"user_id": current_user["id"]}
    )
    if current_count >= MAX_LIMIT:
        raise HTTPException(
            status_code=400,
            detail=f"Storage limit reached. Please delete old articles. (Limit: {MAX_LIMIT})"
        )

    # ── Duplicate check ────────────────────────────────────
    existing = await db.saved_articles.find_one(
        {"user_id": current_user["id"], "article_id": article.article_id}
    )
    if existing:
        raise HTTPException(status_code=409, detail="Article already saved")

    # ── Insert ─────────────────────────────────────────────
    doc = {
        "user_id": current_user["id"],
        "article_id": article.article_id,
        "title": article.title,
        "url": article.url,
        "summary": article.summary,
        "source": article.source,
        "author": article.author,
        "image_url": article.image_url,
        "published_at": article.published_at,
        "sentiment": article.sentiment,
        "categories": article.categories or [],
        "saved_at": datetime.now(timezone.utc),
    }
    await db.saved_articles.insert_one(doc)

    return {
        "ok": True,
        "message": "Article saved successfully",
    }


@router.delete("/{article_id}")
async def unsave_article(
    article_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Remove a saved article by its article_id for the specific user."""
    db = database.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    result = await db.saved_articles.delete_one(
        {"user_id": current_user["id"], "article_id": article_id}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Saved article not found")

    return {"ok": True, "message": "Article removed from saved"}
