from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Uuid, func
from sqlalchemy.orm import relationship
from uuid import uuid4

from database import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("agent.agentId", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    agent = relationship("Agent", back_populates="chats")
    messages = relationship(
        "ChatMessage",
        back_populates="chat",
        cascade="all, delete-orphan",
        order_by="ChatMessage.id",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    chat_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    chat = relationship("Chat", back_populates="messages")