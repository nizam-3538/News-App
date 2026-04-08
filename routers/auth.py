"""
Auth Router — Register / Login / Me.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from dependencies import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
)
from config import ACCESS_TOKEN_EXPIRE_MINUTES
from models import UserCreate, UserOut, Token, VerifyRequest, ForgotPasswordRequest, ResetPasswordRequest
import database
import random
from utils.email import send_verification_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, background_tasks: BackgroundTasks):
    db = database.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    existing_email = await db.users.find_one({"email": user.email.lower()})
    if existing_email:
        if existing_email.get("is_verified"):
            raise HTTPException(status_code=400, detail="Email already registered")
        else:
            # Resume Flow: User exists but isn't verified
            if user.password != user.confirm_password:
                raise HTTPException(status_code=400, detail="Passwords do not match")
                
            hashed_password = await get_password_hash(user.password)
            await db.users.update_one(
                {"email": user.email.lower()},
                {"$set": {"password": hashed_password, "username": user.username}}
            )
            
            otp = str(random.randint(100000, 999999))
            expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
            await db.otp_codes.update_one(
                {"email": user.email.lower()},
                {"$set": {"code": otp, "expires_at": expires_at}},
                upsert=True
            )
            print(f"📧 [RESUME] VERIFICATION CODE FOR {user.email}: {otp}")
            background_tasks.add_task(send_verification_email, user.email.lower(), otp)
            return {"ok": True, "email": user.email.lower(), "status": "pending", "message": "Verification required"}

    existing_username = await db.users.find_one({"username": user.username})
    if existing_username and existing_username["email"] != user.email.lower():
        raise HTTPException(status_code=400, detail="Username already taken")

    if user.password != user.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    hashed_password = await get_password_hash(user.password)
    user_dict = {
        "username": user.username,
        "email": user.email.lower(),
        "password": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "is_active": True,
        "is_verified": False,
    }
    await db.users.insert_one(user_dict)

    # Generate OTP
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    await db.otp_codes.insert_one({
        "email": user.email.lower(),
        "code": otp,
        "expires_at": expires_at
    })

    print(f"📧 VERIFICATION CODE FOR {user.email}: {otp}")
    background_tasks.add_task(send_verification_email, user.email.lower(), otp)

    return {"ok": True, "email": user.email.lower(), "status": "pending", "message": "OTP sent to email. Please verify."}

@router.post("/verify-email")
async def verify_email(payload: VerifyRequest):
    db = database.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    record = await db.otp_codes.find_one({
        "email": payload.email.lower(),
        "code": payload.otp
    })

    if not record:
        raise HTTPException(status_code=400, detail="Invalid OTP code")

    # Ensure tz-awareness
    expiry = record["expires_at"]
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP code expired")

    await db.users.update_one(
        {"email": payload.email.lower()},
        {"$set": {"is_verified": True}}
    )
    await db.otp_codes.delete_many({"email": payload.email.lower()})

    return {"ok": True, "message": "Email verified successfully"}

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    db = database.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    user = await db.users.find_one({"email": payload.email.lower()})
    if not user:
        # Avoid user enumeration by returning success regardless, 
        # but don't perform any actions.
        return {"ok": True, "message": "If this email exists, a reset code has been sent."}

    # Generate OTP
    otp = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    await db.otp_codes.update_one(
        {"email": payload.email.lower()},
        {"$set": {"code": otp, "expires_at": expires_at}},
        upsert=True
    )

    print(f"🔑 RESET CODE FOR {payload.email}: {otp}")
    background_tasks.add_task(send_password_reset_email, payload.email.lower(), otp)

    return {"ok": True, "message": "Password reset code sent."}

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest):
    db = database.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    record = await db.otp_codes.find_one({
        "email": payload.email.lower(),
        "code": payload.otp
    })

    if not record:
        raise HTTPException(status_code=400, detail="Invalid reset code.")

    expiry = record["expires_at"]
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if expiry < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset code expired.")

    # Update user password
    hashed_password = await get_password_hash(payload.new_password)
    await db.users.update_one(
        {"email": payload.email.lower()},
        {"$set": {"password": hashed_password}}
    )

    # Delete the used OTP
    await db.otp_codes.delete_many({"email": payload.email.lower()})

    return {"ok": True, "message": "Password reset successfully."}


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    db = database.get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Try email first, then username
    user = await db.users.find_one({"email": form_data.username.lower()})
    if not user:
        user = await db.users.find_one({"username": form_data.username})

    if not user or not await verify_password(form_data.password, user.get("password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.get("is_verified") is False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please verify your email first.",
        )

    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Fetch current user details."""
    db = database.get_db()
    user = await db.users.find_one({"email": current_user["email"]})
    return UserOut(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"],
        is_verified=user.get("is_verified", True) # Legacy users are verified by default
    )
