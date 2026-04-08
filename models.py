"""
Pydantic request / response schemas for the News App API.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ━━━━━━━━━━━━━━━━━━━  AUTH  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    created_at: datetime
    is_verified: bool = False

class VerifyRequest(BaseModel):
    email: str
    otp: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    otp: str
    new_password: str = Field(..., min_length=8)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


# ━━━━━━━━━━━━━━━━━━  SAVED ARTICLES  ━━━━━━━━━━━━━━━━━━━━

class SaveArticleRequest(BaseModel):
    article_id: str = Field(..., max_length=300)
    title: str = Field(..., max_length=500)
    url: str = Field(..., max_length=1000)
    summary: Optional[str] = Field(None, max_length=2000)
    source: Optional[str] = Field(None, max_length=100)
    author: Optional[str] = Field(None, max_length=200)
    image_url: Optional[str] = Field(None, max_length=1000)
    published_at: Optional[str] = None
    sentiment: Optional[str] = Field(None, pattern="^(Positive|Negative|Neutral)$")
    categories: Optional[List[str]] = []
    tags: List[str] = []
    note: str = ""


class SavedArticleOut(BaseModel):
    user_id: str
    article_id: str
    title: str
    url: str
    summary: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    published_at: Optional[str] = None
    sentiment: Optional[str] = None
    categories: Optional[List[str]] = []
    tags: List[str] = []
    note: str = ""
    saved_at: datetime


# ━━━━━━━━━━━━━━━━━━━  NEWS  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ArticleOut(BaseModel):
    id: str
    title: str
    link: str
    summary: Optional[str] = None
    content: Optional[str] = None
    published_at: Optional[str] = None
    source: Optional[str] = None
    author: Optional[str] = None
    image_url: Optional[str] = None
    sentiment: str = "Neutral"
    categories: List[str] = []


class NewsResponse(BaseModel):
    success: bool
    data: List[ArticleOut]
    meta: dict


# ━━━━━━━━━━━━━━━━━━━  CHAT  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=10000)
    article_text: str = Field(..., min_length=1, max_length=50000)
    language: str = "English"
    history: Optional[List[dict]] = None


class ChatResponse(BaseModel):
    ok: bool
    answer: str
    model: str
    grounded: bool
