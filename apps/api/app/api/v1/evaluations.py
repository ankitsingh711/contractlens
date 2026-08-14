import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.evaluation import (
    EvaluationRunDetailResponse,
    EvaluationRunListResponse,
    EvaluationRunResponse,
)
from app.services.evaluation_service import (
    get_evaluation_run,
    list_evaluation_runs,
    run_evaluation,
    start_evaluation,
)

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/run", response_model=EvaluationRunResponse)
async def trigger_evaluation_run(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    eval_run = await start_evaluation(db, current_user.organization_id)
    background_tasks.add_task(
        run_evaluation, eval_run.id, current_user.organization_id, current_user.id
    )
    return eval_run


@router.get("", response_model=EvaluationRunListResponse)
async def get_evaluation_runs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    runs = await list_evaluation_runs(db, current_user.organization_id)
    return EvaluationRunListResponse(evaluation_runs=runs)


@router.get("/{evaluation_run_id}", response_model=EvaluationRunDetailResponse)
async def get_evaluation_run_by_id(
    evaluation_run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_evaluation_run(db, evaluation_run_id, current_user.organization_id)
