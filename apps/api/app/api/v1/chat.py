import json

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.agent_service import stream_agent

router = APIRouter(tags=["chat"])


def _sse_format(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


@router.post("/chat")
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    document_ids = [str(d) for d in payload.document_ids] if payload.document_ids else []

    async def event_stream():
        async for event in stream_agent(
            db,
            organization_id=current_user.organization_id,
            user_id=current_user.id,
            query=payload.message,
            document_ids=document_ids,
            conversation_id=payload.conversation_id,
        ):
            yield _sse_format(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
