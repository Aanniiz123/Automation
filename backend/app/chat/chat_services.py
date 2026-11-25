from typing import Literal
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.models.model import Agent
from app.auth.models.model import User
from .models.model import Chat, ChatMessage


async def create_chat(
    db: AsyncSession,
    agent_id: UUID,
    current_user: User,
) -> Chat:
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

    chat = Chat(agent_id=agent.agentId)
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    return chat


async def _get_owned_chat(
    db: AsyncSession,
    chat_id: UUID,
    current_user: User,
) -> Chat:
    result = await db.execute(
        select(Chat)
        .join(Agent, Chat.agent_id == Agent.agentId)
        .where(
            Chat.id == chat_id,
            Agent.user_id == current_user.id,
        )
    )
    chat = result.scalar_one_or_none()

    if chat is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    return chat


async def add_chat_message(
    db: AsyncSession,
    chat_id: UUID,
    content: str,
    current_user: User,
    role: Literal["user", "assistant"] = "user",
) -> ChatMessage:
    chat = await _get_owned_chat(db, chat_id, current_user)

    message = ChatMessage(
        chat_id=chat.id,
        role=role,
        content=content,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def get_chat_messages(
    db: AsyncSession,
    chat_id: UUID,
    current_user: User,
) -> list[ChatMessage]:
    await _get_owned_chat(db, chat_id, current_user)

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.chat_id == chat_id)
        .order_by(ChatMessage.created_at, ChatMessage.id)
    )
    return list(result.scalars().all())