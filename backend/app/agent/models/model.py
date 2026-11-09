from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


class Agent(Base):
    __tablename__ = "agent"

    agentId = Column(Integer, primary_key=True)
    agentName = Column(String(100), unique=True, nullable=False)
    agentDescription = Column(String(255), nullable=True)

    user_id = Column(Integer,ForeignKey("users.id", ondelete="CASCADE"),nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False, 
    )

    user = relationship("User",back_populates="agents")