import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal
from app.evaluation.dataset import DEFAULT_DATASET_VERSION, EvalCase, load_dataset
from app.evaluation.metrics import compute_case_metrics
from app.models.document import Document, DocumentStatus
from app.models.evaluation_result import EvaluationResult
from app.models.evaluation_run import EvaluationRun, EvaluationRunStatus
from app.services.agent_service import run_agent

logger = get_logger("evaluation_service")
settings = get_settings()

# (metric name, higher_is_better) — used both to detect regressions and to
# know which direction "worse" means for each metric.
_TRACKED_METRICS: list[tuple[str, bool]] = [
    ("faithfulness", True),
    ("citation_accuracy", True),
    ("retrieval_recall", True),
    ("retrieval_precision", True),
    ("answer_relevance", True),
    ("hallucination_rate", False),
]


async def start_evaluation(db: AsyncSession, organization_id: uuid.UUID) -> EvaluationRun:
    eval_run = EvaluationRun(
        organization_id=organization_id,
        dataset_version=DEFAULT_DATASET_VERSION,
        status=EvaluationRunStatus.RUNNING,
        results=[],
    )
    db.add(eval_run)
    await db.commit()
    await db.refresh(eval_run, attribute_names=["created_at", "updated_at"])
    return eval_run


async def _run_single_case(
    db: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    case: EvalCase,
    evaluation_run_id: uuid.UUID,
) -> EvaluationResult:
    document = await db.scalar(
        select(Document).where(
            Document.organization_id == organization_id,
            Document.filename == case.document_filename,
            Document.status == DocumentStatus.COMPLETED,
            Document.deleted_at.is_(None),
        )
    )
    if document is None:
        logger.warning(
            "evaluation.document_missing", case_id=case.id, filename=case.document_filename
        )
        return EvaluationResult(
            evaluation_run_id=evaluation_run_id,
            case_id=case.id,
            category=case.category,
            question=case.question,
            expected_answer=case.expected_answer,
            answer=None,
            passed=False,
            abstained=True,
            should_abstain=case.should_abstain,
            retrieval_recall=0.0,
            retrieval_precision=0.0,
            citation_accuracy=0.0,
            faithfulness=0.0,
            answer_relevance=0.0,
            hallucinated=False,
            latency_ms=0.0,
        )

    agent_run, _conversation = await run_agent(
        db,
        organization_id=organization_id,
        user_id=user_id,
        query=case.question,
        document_ids=[str(document.id)],
    )

    retrieve_step = next((s for s in agent_run.steps if s.step_name == "retrieve"), None)
    retrieved_chunks = (retrieve_step.output.get("retrieved_chunks", []) if retrieve_step else [])
    retrieved_sections = {c["section"] for c in retrieved_chunks if c.get("section")}
    citation_sections = {c["section"] for c in agent_run.citations if c.get("section")}
    abstained = len(agent_run.citations) == 0

    metrics = compute_case_metrics(
        should_abstain=case.should_abstain,
        abstained=abstained,
        retrieved_sections=retrieved_sections,
        expected_sections=set(case.expected_sources),
        citation_sections=citation_sections,
        answer=agent_run.answer,
        expected_answer=case.expected_answer,
    )

    return EvaluationResult(
        evaluation_run_id=evaluation_run_id,
        agent_run_id=agent_run.id,
        case_id=case.id,
        category=case.category,
        question=case.question,
        expected_answer=case.expected_answer,
        answer=agent_run.answer,
        passed=metrics.passed,
        abstained=abstained,
        should_abstain=case.should_abstain,
        retrieval_recall=metrics.retrieval_recall,
        retrieval_precision=metrics.retrieval_precision,
        citation_accuracy=metrics.citation_accuracy,
        faithfulness=metrics.faithfulness,
        answer_relevance=metrics.answer_relevance,
        hallucinated=metrics.hallucinated,
        latency_ms=agent_run.latency_ms or 0.0,
        input_tokens=agent_run.input_tokens,
        output_tokens=agent_run.output_tokens,
        cost_usd=agent_run.estimated_cost_usd or 0.0,
    )


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


async def _find_baseline(
    db: AsyncSession, organization_id: uuid.UUID, dataset_version: str, exclude_id: uuid.UUID
) -> EvaluationRun | None:
    stmt = (
        select(EvaluationRun)
        .where(
            EvaluationRun.organization_id == organization_id,
            EvaluationRun.dataset_version == dataset_version,
            EvaluationRun.status == EvaluationRunStatus.COMPLETED,
            EvaluationRun.id != exclude_id,
        )
        .order_by(EvaluationRun.created_at.desc())
        .limit(1)
    )
    return await db.scalar(stmt)


def _detect_regressions(current: EvaluationRun, baseline: EvaluationRun) -> list[dict]:
    regressions = []
    for metric_name, higher_is_better in _TRACKED_METRICS:
        current_value = getattr(current, metric_name)
        baseline_value = getattr(baseline, metric_name)
        if current_value is None or baseline_value is None:
            continue
        delta = current_value - baseline_value
        regressed = (delta < -settings.REGRESSION_THRESHOLD) if higher_is_better else (
            delta > settings.REGRESSION_THRESHOLD
        )
        if regressed:
            regressions.append(
                {
                    "metric": metric_name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "delta": delta,
                }
            )
    return regressions


async def run_evaluation(evaluation_run_id: uuid.UUID, organization_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Executes every case in the dataset against this organization's
    documents, persists one EvaluationResult per case (each with its own
    AgentRun — reusing the exact chat pipeline being evaluated, not a
    separate code path), aggregates metrics, and compares against the
    most recent prior COMPLETED run for the same dataset version to flag
    regressions. Runs as a background task with its own DB session.
    """
    async with AsyncSessionLocal() as db:
        eval_run = await db.get(EvaluationRun, evaluation_run_id)
        if eval_run is None:
            logger.error("run_evaluation.missing_run", evaluation_run_id=str(evaluation_run_id))
            return

        try:
            dataset = load_dataset(eval_run.dataset_version)
            results: list[EvaluationResult] = []
            for case in dataset.cases:
                result = await _run_single_case(db, organization_id, user_id, case, eval_run.id)
                db.add(result)
                results.append(result)

            eval_run.total_cases = len(results)
            eval_run.passed_cases = sum(1 for r in results if r.passed)
            eval_run.failed_cases = eval_run.total_cases - eval_run.passed_cases
            eval_run.faithfulness = _mean([r.faithfulness for r in results])
            eval_run.citation_accuracy = _mean([r.citation_accuracy for r in results])
            eval_run.retrieval_recall = _mean([r.retrieval_recall for r in results])
            eval_run.retrieval_precision = _mean([r.retrieval_precision for r in results])
            eval_run.hallucination_rate = _mean([1.0 if r.hallucinated else 0.0 for r in results])
            eval_run.answer_relevance = _mean([r.answer_relevance for r in results])
            eval_run.avg_latency_ms = _mean([r.latency_ms for r in results])
            eval_run.avg_input_tokens = _mean([float(r.input_tokens) for r in results])
            eval_run.avg_output_tokens = _mean([float(r.output_tokens) for r in results])
            eval_run.avg_cost_usd = _mean([r.cost_usd for r in results])

            baseline = await _find_baseline(
                db, organization_id, eval_run.dataset_version, exclude_id=eval_run.id
            )
            if baseline is not None:
                eval_run.baseline_run_id = baseline.id
                eval_run.regressions = _detect_regressions(eval_run, baseline)

            eval_run.status = EvaluationRunStatus.COMPLETED
            await db.commit()
            logger.info(
                "run_evaluation.completed",
                evaluation_run_id=str(evaluation_run_id),
                total_cases=eval_run.total_cases,
                passed_cases=eval_run.passed_cases,
                regression_count=len(eval_run.regressions),
            )
        except Exception as exc:
            await db.rollback()
            eval_run = await db.get(EvaluationRun, evaluation_run_id)
            eval_run.status = EvaluationRunStatus.FAILED
            eval_run.error_message = "An unexpected error occurred while running the evaluation."
            await db.commit()
            logger.error(
                "run_evaluation.failed", evaluation_run_id=str(evaluation_run_id), error=str(exc)
            )


async def get_evaluation_run(
    db: AsyncSession, evaluation_run_id: uuid.UUID, organization_id: uuid.UUID
) -> EvaluationRun:
    stmt = (
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .where(EvaluationRun.id == evaluation_run_id)
    )
    eval_run = (await db.execute(stmt)).scalar_one_or_none()
    if eval_run is None:
        raise NotFoundError("Evaluation run not found.")
    if eval_run.organization_id != organization_id:
        raise ForbiddenError("You do not have access to this evaluation run.")
    return eval_run


async def list_evaluation_runs(
    db: AsyncSession, organization_id: uuid.UUID, limit: int = 20
) -> list[EvaluationRun]:
    stmt = (
        select(EvaluationRun)
        .where(EvaluationRun.organization_id == organization_id)
        .order_by(EvaluationRun.created_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())
