from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    Uuid,
    func,
)
from sqlalchemy.orm import relationship
from uuid import uuid4

from database import Base


class Agent(Base):
    __tablename__ = "agent"

    agentId = Column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    agentName = Column(String(100), unique=True, nullable=False)
    agentDescription = Column(String(255), nullable=True)

    user_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False, 
    )

    user = relationship("User",back_populates="agents")
    chats = relationship(
        "Chat",
        back_populates="agent",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )