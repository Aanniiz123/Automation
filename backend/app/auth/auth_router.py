import random
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.auth_services import (
    EMAIL_VERIFY_TOKEN_TYPE,
    PASSWORD_RESET_TOKEN_TYPE,
    authenticate_google_user,
    create_password_reset_token,
    create_user,
    create_user_token,
    decode_token,
    get_password_hash,
    revoke_refresh_token,
    send_otp_email,
    send_password_reset_email,
    verify_password,
)
from app.auth.dependencies import get_current_user
from app.auth.models.model import User
from app.auth.models.scheme import (
    ForgotPasswordRequest,
    GoogleLoginRequest,
    LoginRequest,
    LogoutRequest,
    RegisterRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
    VerifyOTPRequest,
)
from core.config import settings
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await create_user(db, payload)

    otp = f"{random.randint(100000, 999999)}"
    user.otp = otp
    user.otp_expiry = _utcnow() + timedelta(minutes=10)
    user_id = user.id
    user_email = user.email
    await db.commit()

    print(f"\nDEBUG: OTP for {user_email} is {otp}\n")

    try:
        await send_otp_email(user_email, otp)
    except Exception as exc:
        print(f"Failed to send OTP email: {exc}")

    return {
        "message": "User registered successfully. Please verify your email with the OTP sent.",
        "user_id": user_id,
        "email": user_email,
    }


@router.post("/verify-email")
async def verify_email_token(payload: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    try:
        decoded = decode_token(payload.token, EMAIL_VERIFY_TOKEN_TYPE)
        user_id = int(decoded["sub"])
    except (InvalidTokenError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already verified",
        )

    user.is_verified = True
    await db.commit()
    return {"message": "Email verified successfully"}


@router.post("/verify-otp")
async def verify_otp(payload: VerifyOTPRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.otp or not user.otp_expiry:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    expiry = user.otp_expiry
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if user.otp != payload.otp or expiry < _utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    user.is_verified = True
    user.otp = None
    user.otp_expiry = None
    user_id = user.id
    await db.commit()

    return {
        "message": "OTP verified successfully",
        **(await create_user_token(db, user_id)),
    }



@router.post("/login")
async def login_user(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Google sign-in. Please continue with Google.",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return await create_user_token(db, user.id)


@router.get("/google")
async def google_login(payload: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    return await authenticate_google_user(db, payload.id_token)



@router.get("/refresh")
async def refresh_access_token(
    current_user: User = Depends(get_current_user)):
    return {
        "refresh_token": current_user.refresh_tokens,
    }

@router.get("/me")
async def get_logged_in_user(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
    }


@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is not None and user.hashed_password:
        reset_token = create_password_reset_token(
            {"sub": str(user.id)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        try:
            await send_password_reset_email(user.email, reset_token)
        except Exception as exc:
            print(f"Failed to send password reset email: {exc}")

    return {"message": "If the email exists, a password reset link has been sent."}


@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)
):
    try:
        decoded = decode_token(payload.token, PASSWORD_RESET_TOKEN_TYPE)
        user_id = int(decoded["sub"])
    except (InvalidTokenError, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    return {"message": "Password reset successful"}


@router.post("/logout")
async def logout_user(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await revoke_refresh_token(db, payload.refresh_token)
    return {
        "message": "Logout successful",
        "user_id": current_user.id,
    }

