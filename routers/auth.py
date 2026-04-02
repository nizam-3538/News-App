"""
Auth Router — Register / Login / Me.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm

from dependencies import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from models import UserCreate, UserOut, Token
import database

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    db = database.get_db()
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


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = database.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Try email first, then username
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


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    db = database.get_db()
    user = await db.users.find_one({"email": current_user["email"]})
    return {
        "id": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "created_at": user["created_at"],
    }
