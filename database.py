"""
Async MongoDB connection manager using Motor.
The `db` reference is set during FastAPI lifespan startup.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGODB_URI, DB_NAME

client: AsyncIOMotorClient | None = None
db = None


async def connect():
    """Open the Motor client and set the module-level `db` handle."""
    global client, db
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]

    # ── Indexes ────────────────────────────────────────────
    # Users
    await db.users.create_index("email", unique=True)
    await db.users.create_index("username", unique=True)

    # Saved articles – compound unique (one save per user+article)
    await db.saved_articles.create_index(
        [("user_id", 1), ("article_id", 1)], unique=True
    )
    # Fast "newest-first" retrieval per user
    await db.saved_articles.create_index([("user_id", 1), ("saved_at", -1)])

    print(f"[DB] Connected to MongoDB: {DB_NAME}")


async def disconnect():
    """Gracefully close the Motor client."""
    global client
    if client:
        client.close()
        print("[DB] MongoDB connection closed.")


def get_db():
    """Return the active database handle (used as a FastAPI dependency)."""
    return db
