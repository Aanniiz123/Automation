from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime,
    UniqueConstraint, BigInteger, Uuid, func,
)
from sqlalchemy.orm import relationship
from uuid import uuid4
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    otp = Column(String(6), nullable=True)
    otp_expiry = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    oauth_accounts = relationship(
        "OAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    agents = relationship(
        "Agent",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True
    )


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_account_id",
            name="uq_oauth_provider_account",
        ),
    )

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)

    user_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    provider = Column(String(50), nullable=False)
    provider_account_id = Column(String(255), nullable=False)
    access_token = Column(String(2048), nullable=True)
    refresh_token = Column(String(2048), nullable=True)
    expires_at = Column(BigInteger, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="oauth_accounts")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)

    user_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    token_hash = Column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    expires_at = Column(BigInteger, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="refresh_tokens")
