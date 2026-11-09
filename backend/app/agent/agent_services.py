
from sqlalchemy.ext.asyncio import AsyncSession
from .models.scheme import AgentCreate, AgentDelete
from .models.model import Agent
from app.auth.models.model import User


from sqlalchemy import select

from fastapi import HTTPException, status


async def create_agents(db : AsyncSession,
                        agent_create: AgentCreate,
                        current_user : User
                        ) -> Agent :

    agent = await db.execute(select(Agent). where(Agent.agentName == agent_create.agentName))
    existing_agent = agent.scalar_one_or_none()

    if existing_agent:
        raise HTTPException(
            status_code= status.HTTP_400_BAD_REQUEST,
            detail="Agent name exist"
        )

    new_agent = Agent(
        agentName = agent_create.agentName,
        agentDescription = agent_create.agentDescription,
        user_id = current_user.id

    )
    try:
        db.add(new_agent)

        await db.commit()
        await db.refresh(new_agent) 

        return new_agent

    except Exception:
        await db.rollback()
        raise


async def delete_agents(
    db: AsyncSession,
    agent_id: int,
    current_user: User,
) -> None:
    
    result = await db.execute(
        select(Agent).where(
            Agent.agentId == agent_id,
            Agent.user_id == current_user.id,
        )
    )
    agent = result.scalar_one_or_none()

    if agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    try:
        await db.delete(agent)
        await db.commit()

        result = await db.execute(select(Agent).order_by(Agent.agentId))

        rows = result.scalars().all()

        for new_id, row in enumerate(rows, start=1):
            row.agentId = new_id

        await db.commit()

    except Exception:
        await db.rollback()
        raise