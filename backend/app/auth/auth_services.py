import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

import aiosmtplib
import jwt
from email.message import EmailMessage
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models.model import OAuthAccount, RefreshToken, User
from app.auth.models.scheme import UserCreate
from core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DUMMY_HASH = pwd_context.hash("dummy_password")

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
EMAIL_VERIFY_TOKEN_TYPE = "email_verify"
PASSWORD_RESET_TOKEN_TYPE = "password_reset"


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        pwd_context.verify(plain_password, DUMMY_HASH)
        return False
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_token(
    data: dict[str, Any],
    token_type: str,
    expires_delta: timedelta | None = None,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = data.copy()
    now = _utcnow()
    to_encode.update({"exp": now + expires_delta, "iat": now, "typ": token_type})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    return create_token(data, ACCESS_TOKEN_TYPE, expires_delta)


def create_refresh_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    return create_token(data, REFRESH_TOKEN_TYPE, expires_delta)


def create_verification_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    return create_token(data, EMAIL_VERIFY_TOKEN_TYPE, expires_delta)


def create_password_reset_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    return create_token(data, PASSWORD_RESET_TOKEN_TYPE, expires_delta)


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError("Invalid token") from exc

    if payload.get("typ") != expected_type:
        raise InvalidTokenError("Invalid token type")
    if payload.get("sub") is None:
        raise InvalidTokenError("Missing subject")
    return payload


async def create_user(db: AsyncSession, user_create: UserCreate) -> User:
    result = await db.execute(select(User).where(User.email == user_create.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    new_user = User(
        email=user_create.email,
        hashed_password=get_password_hash(user_create.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def create_user_token(db: AsyncSession, user_id: int) -> dict:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=access_token_expires,
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user_id)},
        expires_delta=refresh_token_expires,
    )

    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hash_token(refresh_token),
            expires_at=int((_utcnow() + refresh_token_expires).timestamp()),
            revoked=False,
        )
    )
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


async def get_valid_refresh_token(
    db: AsyncSession, refresh_token: str
) -> RefreshToken:
    try:
        payload = decode_token(refresh_token, REFRESH_TOKEN_TYPE)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_token(refresh_token),
            RefreshToken.revoked.is_(False),
        )
    )
    stored = result.scalar_one_or_none()
    now_ts = int(_utcnow().timestamp())

    if stored is None or stored.expires_at < now_ts:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if str(stored.user_id) != str(payload["sub"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return stored


async def rotate_refresh_token(db: AsyncSession, refresh_token: str) -> dict:
    stored = await get_valid_refresh_token(db, refresh_token)
    stored.revoked = True
    user_id = stored.user_id
    await db.flush()
    return await create_user_token(db, user_id)


async def revoke_refresh_token(db: AsyncSession, refresh_token: str) -> None:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
    )
    stored = result.scalar_one_or_none()
    if stored is not None and not stored.revoked:
        stored.revoked = True
        await db.commit()


def build_auth_link(token: str, route: str) -> str:
    base_url = (
        settings.FRONTEND_URL or settings.BACKEND_URL or "http://localhost:8000"
    ).rstrip("/")
    return f"{base_url}{route}?token={token}"


async def _send_email(to_email: str, subject: str, body: str) -> None:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"\nSMTP is not configured. Email to {to_email} skipped.\n{body}\n")
        return

    message = EmailMessage()
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=settings.SMTP_USE_TLS,
    )


async def send_verification_email(email: str, token: str) -> None:
    verification_url = build_auth_link(token, "/auth/verify-email")
    await _send_email(
        email,
        "Verify Your Email Address",
        f"Please verify your email by opening this link:\n{verification_url}",
    )


async def send_password_reset_email(email: str, token: str) -> None:
    reset_url = build_auth_link(token, "/auth/reset-password")
    await _send_email(
        email,
        "Password Reset Request",
        f"Reset your password by opening this link:\n{reset_url}",
    )


async def send_otp_email(email: str, otp: str) -> None:
    await _send_email(
        email,
        "Your One-Time Password (OTP)",
        f"Your OTP is: {otp}\nIt expires in 10 minutes.",
    )


def verify_google_token(token: str) -> dict:
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured",
        )

    try:
        return id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        ) from exc


async def authenticate_google_user(db: AsyncSession, token: str) -> dict:
    google_user = verify_google_token(token)
    email = google_user.get("email")
    provider_account_id = google_user.get("sub")

    if not email or not provider_account_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google token is missing email or user id",
        )

    if not google_user.get("email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google email is not verified",
        )

    result = await db.execute(
        select(OAuthAccount).where(
            OAuthAccount.provider == "google",
            OAuthAccount.provider_account_id == provider_account_id,
        )
    )
    oauth_account = result.scalar_one_or_none()

    if oauth_account:
        user_result = await db.execute(select(User).where(User.id == oauth_account.user_id))
        user = user_result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="OAuth account is not linked to a user",
            )
    else:
        user_result = await db.execute(select(User).where(User.email == email))
        user = user_result.scalar_one_or_none()

        if user is None:
            user = User(
                email=email,
                hashed_password=None,
                is_verified=True,
            )
            db.add(user)
            await db.flush()

        db.add(
            OAuthAccount(
                user_id=user.id,
                provider="google",
                provider_account_id=provider_account_id,
            )
        )
        user.is_verified = True
        await db.commit()
        await db.refresh(user)

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    return await create_user_token(db, int(user.id))
