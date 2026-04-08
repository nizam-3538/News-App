"""
News App API — FastAPI backend entry point.
Includes: Auth, News (VADER sentiment), Saved Articles (500 limit), AI Chat (Gemini).
"""

import os
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from models import ChatRequest, UserOut, Token
from dependencies import get_current_user

# ─── Load environment variables ──────────────────────────
load_dotenv()

from config import (
    MONGODB_URI, 
    DB_NAME, 
    JWT_SECRET, 
    JWT_ALGORITHM, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALLOWED_ORIGINS
)

# ─── Database handles (set during lifespan) ───────────────
db_client: Optional[AsyncIOMotorClient] = None
db = None


# ─── Lifespan ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_client, db

    # Also set the database module's handles for the routers
    import database as db_module

    try:
        db_client = AsyncIOMotorClient(
            MONGODB_URI, serverSelectionTimeoutMS=5000
        )
        temp_db = db_client[DB_NAME]

        # Verify connectivity with a fast ping, then create indexes
        await db_client.admin.command("ping")

        await temp_db.users.create_index("email", unique=True)
        await temp_db.users.create_index("username", unique=True)
        await temp_db.saved_articles.create_index(
            [("user_id", 1), ("article_id", 1)], unique=True
        )
        await temp_db.saved_articles.create_index([("user_id", 1), ("saved_at", -1)])

        db = temp_db
        # Sync the database module so routers can use it
        db_module.client = db_client
        db_module.db = db

        print("[STARTUP] MongoDB connected and indexes created.")
    except Exception as exc:
        print(f"[STARTUP] MongoDB not available: {exc}")
        db_client = None
        db = None
        db_module.client = None
        db_module.db = None

    yield

    if db_client:
        db_client.close()
        print("[SHUTDOWN] MongoDB connection closed.")


# ─── App creation ─────────────────────────────────────────
app = FastAPI(
    title="News App API",
    description="Backend API for the Modern News Aggregator",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Include modular routers (Phase 2+) ──────────────────
from routers import auth as auth_router
from routers import news as news_router
from routers import saved as saved_router
from routers import chat as chat_router

app.include_router(auth_router.router)
app.include_router(news_router.router)
app.include_router(saved_router.router, prefix="/api/saved")
app.include_router(chat_router.router)


# ━━━━━━━━━━━━━━━━━━━━  ROUTES  ━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected" if db is not None else "disconnected",
    }


# ── Phase 2: News Fetching & AI Integration (Protected Routes) ──

@app.get("/api/news", tags=["News"])
async def get_news_inline(
    q: str = "",
    limit: int = 100,
    current_user: dict = Depends(get_current_user),
):
    """
    Fetch news (defaulting to Top Headlines) and tag each article with VADER sentiment.
    Delegates external API logic to services/news_fetcher.py. 
    Requires JWT Authentication.
    """
    from services.news_fetcher import fetch_all_news
    articles = await fetch_all_news(query=q, limit=limit)
    return {
        "success": True,
        "data": articles,
        "meta": {"total": len(articles)}
    }


@app.post("/api/chat", tags=["AI Chat"])
async def chat_inline(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Ask a question about an article.
    Delegates to services/ai_engine.py which enforces strict grounding via prompt.
    Requires JWT Authentication.
    """
    from services.ai_engine import grounded_chat
    result = await grounded_chat(
        article_text=body.article_text,
        question=body.question,
        language=body.language,
        history=body.history
    )
    return {"ok": True, **result}


    return {"ok": True, **result}

