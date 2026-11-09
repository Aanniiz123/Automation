from pydantic import BaseModel, Field
from typing import Dict, List




class AgentCreate(BaseModel):
    userId : int
    agentName : str | None = Field(...)
    agentDescription : str


class AgentDelete(BaseModel):
    agentId : int
