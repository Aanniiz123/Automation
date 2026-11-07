from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int | None = Field(default=None, description="Access token lifetime in seconds")


class TokenData(BaseModel):
    user_id: int | None = Field(
        default=None, description="User ID from the token's 'sub' claim"
    )


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    refresh_token: str



class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=72)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    is_active: bool | None = None


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool = True
    is_verified: bool = False
    created_at: datetime


class UserInDB(UserRead):
    hashed_password: str | None = Field(
        default=None, description="Null for OAuth-only users"
    )


class OAuthAccountRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    provider_account_id: str
    created_at: datetime


class RegisterRequest(UserCreate):
    pass


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)


class VerifyEmailRequest(BaseModel):
    token: str


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class GoogleLoginRequest(BaseModel):
    id_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
