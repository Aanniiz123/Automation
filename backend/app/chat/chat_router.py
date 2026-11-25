from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.models.model import User
from database import get_db
from .chat_services import (
    add_chat_message,
    create_chat as create_chat_service,
    get_chat_messages,
)
from .models.schema import ChatCreate, ChatMessageCreate, ChatMessageRead, ChatRead


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/", response_model=ChatRead, status_code=status.HTTP_201_CREATED)
async def create_chat(
    data: ChatCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_chat_service(db, data.agent_id, current_user)


@router.post(
    "/{chat_id}/messages",
    response_model=ChatMessageRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_message(
    chat_id: UUID,
    data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await add_chat_message(
        db=db,
        chat_id=chat_id,
        content=data.content,
        current_user=current_user,
    )


@router.get("/{chat_id}/messages", response_model=list[ChatMessageRead])
async def list_messages(
    chat_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await get_chat_messages(db, chat_id, current_user)