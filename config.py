"""
Centralized configuration for the News App API.
All environment variables are loaded here as a single source of truth.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Server ───────────────────────────────────────────────
PORT = int(os.getenv("PORT", "8000"))
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ─── MongoDB ──────────────────────────────────────────────
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/news-app")
DB_NAME = os.getenv("DB_NAME", "news-app")

# ─── JWT / Auth ───────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-default-key-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# ─── External APIs ───────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "")
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "your-gmail@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-16-letter-app-password")

# ─── Limits ───────────────────────────────────────────────
MAX_SAVED_ARTICLES = 500
MAX_NEWS_RESULTS = 200

# ─── CORS ─────────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
