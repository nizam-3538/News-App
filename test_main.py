"""
Phase 1 Tests — Auth routes (Register / Login / Me / Health).

Uses an in-memory fake MongoDB so tests pass without a running database.
"""

import pytest
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from bson import ObjectId

import main  # noqa: E402 — imported before TestClient so we can patch `db`
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  In-memory fake MongoDB collection
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class _FakeInsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class FakeCollection:
    """Minimal async-compatible MongoDB collection backed by a Python list."""

    def __init__(self):
        self._docs: list[dict] = []

    async def create_index(self, *_args, **_kwargs):
        pass  # no-op — tests don't need real indexes

    async def find_one(self, query: dict):
        for doc in self._docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    async def insert_one(self, document: dict):
        doc = dict(document)
        doc.setdefault("_id", ObjectId())
        self._docs.append(doc)
        return _FakeInsertResult(doc["_id"])

    async def count_documents(self, query: dict) -> int:
        return sum(
            1
            for doc in self._docs
            if all(doc.get(k) == v for k, v in query.items())
        )


class FakeDB:
    """Fake Motor database with two collections used in Phase 1."""

    def __init__(self):
        self.users = FakeCollection()
        self.saved_articles = FakeCollection()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Fixtures
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@pytest.fixture()
def client():
    """
    Create a TestClient with a fake lifespan that injects FakeDB
    instead of connecting to real MongoDB.
    """
    fake_db = FakeDB()

    @asynccontextmanager
    async def _mock_lifespan(_app):
        import database
        main.db = fake_db
        database.db = fake_db
        yield
        main.db = None
        database.db = None

    # Swap the lifespan before creating the test client
    original_lifespan = main.app.router.lifespan_context
    main.app.router.lifespan_context = _mock_lifespan

    with TestClient(main.app) as c:
        yield c

    # Restore
    main.app.router.lifespan_context = original_lifespan


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Tests
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


def test_health_check(client):
    """GET /health should return 200 and database = connected."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_register_returns_token(client):
    """POST /auth/register should return 201 with a bearer token."""
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password123!",
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    """Registering the same email twice should return 400."""
    payload = {
        "username": "user_one",
        "email": "duplicate@example.com",
        "password": "Password123!",
    }
    resp1 = client.post("/auth/register", json=payload)
    assert resp1.status_code == 201

    payload["username"] = "user_two"  # same email, different username
    resp2 = client.post("/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already registered" in resp2.json()["detail"].lower()


def test_register_duplicate_username(client):
    """Registering the same username twice should return 400."""
    payload = {
        "username": "dupe_user",
        "email": "first@example.com",
        "password": "Password123!",
    }
    resp1 = client.post("/auth/register", json=payload)
    assert resp1.status_code == 201

    payload["email"] = "second@example.com"  # same username, different email
    resp2 = client.post("/auth/register", json=payload)
    assert resp2.status_code == 400
    assert "already taken" in resp2.json()["detail"].lower()


def test_register_validation_short_password(client):
    """Password shorter than 8 chars should be rejected (422)."""
    payload = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "short",
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 422  # Pydantic validation error


def test_register_validation_bad_email(client):
    """Invalid email format should be rejected (422)."""
    payload = {
        "username": "testuser",
        "email": "not-an-email",
        "password": "Password123!",
    }
    resp = client.post("/auth/register", json=payload)
    assert resp.status_code == 422


def test_login_with_email(client):
    """Register → login with email should return 200 + token."""
    # Register
    payload = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "Password123!",
    }
    client.post("/auth/register", json=payload)

    # Login (OAuth2 form uses 'username' field for the identifier)
    login_data = {
        "username": "login@example.com",
        "password": "Password123!",
    }
    resp = client.post("/auth/login", data=login_data)
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_with_username(client):
    """Register → login with username should return 200 + token."""
    payload = {
        "username": "loginbyname",
        "email": "byname@example.com",
        "password": "Password123!",
    }
    client.post("/auth/register", json=payload)

    login_data = {
        "username": "loginbyname",
        "password": "Password123!",
    }
    resp = client.post("/auth/login", data=login_data)
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    """Login with wrong password should return 401."""
    payload = {
        "username": "wrongpw",
        "email": "wrongpw@example.com",
        "password": "Password123!",
    }
    client.post("/auth/register", json=payload)

    login_data = {
        "username": "wrongpw@example.com",
        "password": "WrongPassword!",
    }
    resp = client.post("/auth/login", data=login_data)
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    """Login with an unregistered user should return 401."""
    login_data = {
        "username": "ghost@example.com",
        "password": "Password123!",
    }
    resp = client.post("/auth/login", data=login_data)
    assert resp.status_code == 401


def test_get_me_with_token(client):
    """GET /auth/me with a valid JWT should return user info."""
    # Register
    payload = {
        "username": "meuser",
        "email": "me@example.com",
        "password": "Password123!",
    }
    reg_resp = client.post("/auth/register", json=payload)
    token = reg_resp.json()["access_token"]

    # Fetch profile
    resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "meuser"
    assert data["email"] == "me@example.com"
    assert "id" in data
    assert "created_at" in data


def test_get_me_without_token(client):
    """GET /auth/me without a token should return 401."""
    resp = client.get("/auth/me")
    assert resp.status_code == 401


def test_get_me_with_invalid_token(client):
    """GET /auth/me with a garbage token should return 401."""
    resp = client.get("/auth/me", headers={"Authorization": "Bearer invalidtoken123"})
    assert resp.status_code == 401


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Phase 2 Tests (News Fetcher & AI Chat)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def test_api_news_unauthorized(client):
    """GET /api/news without token should return 401."""
    resp = client.get("/api/news")
    assert resp.status_code == 401


@patch("services.news_fetcher.NEWS_API_KEY", "dummy")
@patch("services.news_fetcher.GNEWS_API_KEY", "dummy")
@patch("services.news_fetcher.NEWSDATA_API_KEY", "dummy")
@patch("services.news_fetcher.httpx.AsyncClient.get")
def test_api_news_with_token(mock_get, client):
    """GET /api/news with token should mock HTTP requests and append VADER sentiment."""
    # ── Setup mock response representing GNews API JSON format
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {
        "articles": [
            {
                "title": "Positive Sample", 
                "description": "This is amazingly robust software.", 
                "url": "https://example.com/pos", 
                "source": {"name": "Test Source"}, 
                "publishedAt": "2026-03-30T10:00:00Z"
            },
            {
                "title": "Negative Sample", 
                "description": "This is a terrible disaster.", 
                "url": "https://example.com/neg", 
                "source": {"name": "Test Source"}, 
                "publishedAt": "2026-03-30T10:00:00Z"
            }
        ]
    }
    mock_get.return_value = mock_resp

    # Register & Login
    client.post("/auth/register", json={"username": "newsuser", "email": "news@example.com", "password": "Password123!"})
    token = client.post("/auth/login", data={"username": "news@example.com", "password": "Password123!"}).json()["access_token"]

    resp = client.get("/api/news?q=test", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert len(data["data"]) == 2
    
    # ── Verify VADER tagging 
    articles = data["data"]
    pos_article = next(a for a in articles if a["title"] == "Positive Sample")
    neg_article = next(a for a in articles if a["title"] == "Negative Sample")
    
    assert pos_article["sentiment"] == "Positive"
    assert neg_article["sentiment"] == "Negative"


def test_api_chat_unauthorized(client):
    """POST /api/chat without token should return 401."""
    resp = client.post("/api/chat", json={"article_text": "Sample", "user_question": "What is this?"})
    assert resp.status_code == 401


@patch("services.gemini.genai.Client")
def test_api_chat_with_token(mock_client_class, client):
    """POST /api/chat with token should bypass Gemini and return mocked answer."""
    # ── Setup mock Gemini response
    mock_answer = MagicMock()
    mock_answer.text = "The article discusses amazingly robust software."
    
    mock_client_instance = MagicMock()
    # In google-genai, it's client.aio.models.generate_content for async
    mock_client_instance.aio.models.generate_content = AsyncMock(return_value=mock_answer)
    mock_client_class.return_value = mock_client_instance

    # Register & Login
    client.post("/auth/register", json={"username": "chatuser", "email": "chat@example.com", "password": "Password123!"})
    token = client.post("/auth/login", data={"username": "chat@example.com", "password": "Password123!"}).json()["access_token"]

    payload = {
        "article_text": "This is an article about amazing software.",
        "question": "What is the article about?",
        "language": "English"
    }
    resp = client.post("/api/chat", json=payload, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["answer"] == "The article discusses amazingly robust software."
    assert data["grounded"] is True
