import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.agent_run import AgentRunDetailResponse, AgentRunListResponse
from app.services.agent_service import get_agent_run, list_agent_runs

router = APIRouter(prefix="/agent-runs", tags=["agent-runs"])


@router.get("", response_model=AgentRunListResponse)
async def get_agent_runs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    agent_runs = await list_agent_runs(db, current_user.organization_id)
    return AgentRunListResponse(agent_runs=agent_runs)


@router.get("/{agent_run_id}", response_model=AgentRunDetailResponse)
async def get_agent_run_by_id(
    agent_run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_agent_run(db, agent_run_id, current_user.organization_id)
