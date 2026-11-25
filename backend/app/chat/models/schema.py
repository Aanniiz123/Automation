from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ChatCreate(BaseModel):
    agent_id: UUID
    content: str = Field(...)

class ChatRespone(BaseModel):
    aiResponse: str

class ChatMessageCreate(BaseModel):
    content: str = Field(min_length=1)


class ChatMessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chat_id: UUID
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ChatRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    created_at: datetime


class ChatDetailRead(ChatRead):
    messages: list[ChatMessageRead] = Field(default_factory=list)