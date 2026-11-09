from fastapi import APIRouter, status, Depends
from database import get_db

from sqlalchemy.ext.asyncio import AsyncSession

from .models.scheme import AgentCreate, AgentDelete

from .agent_services import create_agents, delete_agents
from app.auth.models.model import User
from .models.model import Agent
from sqlalchemy import select


from app.auth.dependencies import (
    get_current_user)



router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/create-agent", status_code=status.HTTP_201_CREATED)
async def create_agent(
    data: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):

    agent = await create_agents(db, data, current_user)

    return {
        "message": "Agent successfully created",
        "agent": {
            "agentId": agent.agentId,
            "agentName": agent.agentName,
            "agentDescription": agent.agentDescription,
            "user_id": agent.user_id,
            "created_at": agent.created_at,
        },
    }



@router.get("/get-agent")
async def get_agent(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)):

    result = await db.execute(select(Agent).where(Agent.user_id == current_user.id))
    agents = result.scalars().all()

    return {
        "agents": [
            {
                "agentId": agent.agentId,
                "agentName": agent.agentName,
                "agentDescription": agent.agentDescription,
                "created_at": agent.created_at,
            }
            for agent in agents
        ]
    }



@router.delete("/{agent_id}/delete-agent")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_agents(db, agent_id, current_user)
    return {"message": "Agent deleted successfully"}