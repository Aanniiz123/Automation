from pydantic import BaseModel, Field
from uuid import UUID


class AgentCreate(BaseModel):
    userId: UUID
    agentName: str | None = Field(...)
    agentDescription: str


class AgentDelete(BaseModel):
    agentId: UUID
