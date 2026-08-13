import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ConversationDetailResponse, ConversationListResponse
from app.services.agent_service import get_conversation, list_conversations

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationListResponse)
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    conversations = await list_conversations(db, current_user.organization_id, current_user.id)
    return ConversationListResponse(conversations=conversations)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_by_id(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_conversation(db, conversation_id, current_user.organization_id)
