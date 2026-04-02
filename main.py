"""
News App API — FastAPI backend entry point.
Includes: Auth, News (VADER sentiment), Saved Articles (500 limit), AI Chat (Gemini).
"""

import os
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
import jwt
from dotenv import load_dotenv

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

# ─── Password hashing ────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ─── OAuth2 scheme ────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

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


# ━━━━━━━━━━━━━━━━━━  PYDANTIC MODELS  ━━━━━━━━━━━━━━━━━━━

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None


class ChatRequest(BaseModel):
    article_text: str = Field(..., description="The full or partial text of the article to chat about")
    question: str = Field(..., description="The user's question, which must be answered via the article")
    language: str = "English"


# ━━━━━━━━━━━━━━━━━━  AUTH UTILITIES  ━━━━━━━━━━━━━━━━━━━━

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=15)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Decode JWT → fetch user from DB → return user dict."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user = await db.users.find_one({"email": email})
    if user is None:
        raise credentials_exception

    return {"id": str(user["_id"]), "email": user["email"], "username": user["username"]}


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
    Delegates to services/gemini.py which enforces strict grounding via prompt.
    Requires JWT Authentication.
    """
    from services.gemini import grounded_chat
    result = await grounded_chat(
        article_text=body.article_text,
        question=body.question,
        language=body.language
    )
    return {"ok": True, **result}


# ── Phase 1 auth routes (kept inline for backward compat / test_main.py) ──

@app.post("/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED,
           include_in_schema=False)
async def register_inline(user: UserCreate):
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    existing_email = await db.users.find_one({"email": user.email.lower()})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already registered")

    existing_username = await db.users.find_one({"username": user.username})
    if existing_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = get_password_hash(user.password)
    user_dict = {
        "username": user.username,
        "email": user.email.lower(),
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
    }
    await db.users.insert_one(user_dict)

    access_token = create_access_token(
        data={"sub": user.email.lower()},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/auth/login", response_model=Token, include_in_schema=False)
async def login_inline(form_data: OAuth2PasswordRequestForm = Depends()):
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user = await db.users.find_one({"email": form_data.username.lower()})
    if not user:
        user = await db.users.find_one({"username": form_data.username})

    if not user or not verify_password(form_data.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/auth/me", response_model=UserOut, include_in_schema=False)
async def get_me_inline(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"email": current_user["email"]})
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"],
    }
