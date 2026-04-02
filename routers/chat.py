"""
Chat Router — grounded AI Q&A powered by Gemini.
"""

from fastapi import APIRouter, Depends

from dependencies import get_current_user
from models import ChatRequest, ChatResponse
from services.gemini import grounded_chat

router = APIRouter(prefix="/chat", tags=["AI Chat"])


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
    )
    return {"ok": True, **result}
