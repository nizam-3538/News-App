"""
Chat Router — grounded AI Q&A powered by Gemini.
"""

import re
from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from dependencies import get_current_user
from models import ChatRequest, ChatResponse
from services.ai_engine import grounded_chat, generate_summary, vault_rag_chat
import database

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])


class SummaryRequest(BaseModel):
    history: List[dict]


class VaultChatRequest(BaseModel):
    query: str


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Ask a question about an article.
    Gemini is forced to answer ONLY from the provided article text.
    """
    result = await grounded_chat(
        article_text=body.article_text,
        question=body.question,
        language=body.language,
        history=body.history
    )
    return {"ok": not result.get("error", False), **result}


@router.post("/summary")
async def chat_summary(
    body: SummaryRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generate a concise summary of a chat conversation."""
    result = await generate_summary(history=body.history)
    return result


@router.post("/vault")
async def chat_vault(
    body: VaultChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Search the user's saved articles and use Groq to answer based on the context.
    """
    db = database.get_db()
    if db is None:
        return {"ok": False, "answer": "Database unavailable."}

    # Create a simple OR regex search from the user's query words
    words = [re.escape(w) for w in body.query.split() if w.strip()]
    regex_pattern = "|".join(words) if words else body.query

    query_filter = {
        "user_id": current_user["id"],
        "$or": [
            {"title": {"$regex": regex_pattern, "$options": "i"}},
            {"summary": {"$regex": regex_pattern, "$options": "i"}},
            {"tags": {"$regex": regex_pattern, "$options": "i"}}
        ]
    }

    cursor = db.saved_articles.find(query_filter).limit(5)
    articles = await cursor.to_list(length=5)

    if not articles:
        return {"ok": True, "answer": "I cannot find the answer in your saved articles. Your vault doesn't have any articles matching these keywords."}

    # Augment the context
    context_parts = [f"Article {i+1}: [{a.get('title', 'Untitled')}] - [{a.get('summary', '')}]" for i, a in enumerate(articles)]
    context_text = "\n".join(context_parts)
    
    return await vault_rag_chat(context_text=context_text, question=body.query)
