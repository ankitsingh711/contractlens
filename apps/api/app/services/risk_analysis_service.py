import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.errors import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.core.prompts import load_prompt
from app.db.session import AsyncSessionLocal
from app.models.risk_analysis import RiskAnalysis, RiskAnalysisStatus
from app.models.risk_finding import RiskFinding, RiskSeverity
from app.retrieval import hybrid_search
from app.services.citations import build_evidence_block, validate_citations
from app.services.llm import LLMMessage, get_llm_provider
from app.services.risk_categories import RISK_CATEGORIES, classify_severity

logger = get_logger("risk_analysis_service")
settings = get_settings()

# Severity -> numeric weight used to roll individual findings up into one
# 0-100 risk score. Deliberately coarse (three buckets, not a learned
# model) — see docs/agent.md's pattern of documenting heuristic pieces
# rather than overclaiming intelligence they don't have.
_SEVERITY_WEIGHT = {RiskSeverity.HIGH: 1.0, RiskSeverity.MEDIUM: 0.55, RiskSeverity.LOW: 0.2}


def _compute_risk_score(severities: list[RiskSeverity]) -> int:
    if not severities:
        return 0
    avg = sum(_SEVERITY_WEIGHT[s] for s in severities) / len(severities)
    return round(avg * 100)


async def analyze_document(document_id: uuid.UUID, organization_id: uuid.UUID) -> None:
    """Runs the risk analysis pipeline for one document: for each fixed
    category, retrieve evidence scoped to this document, and only emit a
    finding if the evidence clears the same threshold used for Q&A
    abstention and the generated summary survives citation validation —
    a category with no supporting evidence produces no finding at all,
    never a guessed one.

    Runs as a background task with its own DB session, matching
    document_service.process_document()'s pattern.
    """
    async with AsyncSessionLocal() as db:
        analysis = await db.scalar(
            select(RiskAnalysis)
            .where(RiskAnalysis.document_id == document_id)
            .order_by(RiskAnalysis.created_at.desc())
        )
        if analysis is None:
            logger.error("analyze_document.missing_analysis", document_id=str(document_id))
            return

        try:
            llm = get_llm_provider()
            prompt_template = load_prompt("risk_detection", "v1")
            severities: list[RiskSeverity] = []

            for category in RISK_CATEGORIES:
                result = await hybrid_search(
                    db,
                    category.search_query,
                    organization_id,
                    document_ids=[document_id],
                    top_k=3,
                )
                if not result.chunks or result.evidence_score < settings.EVIDENCE_THRESHOLD:
                    continue

                prompt = prompt_template.format(
                    category_label=category.label,
                    evidence=build_evidence_block(result.chunks),
                )
                response = await llm.complete([LLMMessage(role="user", content=prompt)])
                cleaned_text, citations = validate_citations(response.text, result.chunks)
                if not citations:
                    continue

                evidence_text = " ".join(c.text for c in result.chunks)
                severity = RiskSeverity(classify_severity(category, evidence_text))
                severities.append(severity)

                db.add(
                    RiskFinding(
                        risk_analysis_id=analysis.id,
                        category=category.key,
                        severity=severity,
                        title=category.label,
                        reason=cleaned_text,
                        confidence=result.evidence_score,
                        citations=[
                            {
                                "document_id": c.document_id,
                                "filename": c.filename,
                                "page": c.page,
                                "section": c.section,
                                "heading": c.heading,
                                "chunk_id": c.chunk_id,
                                "quote": c.quote,
                            }
                            for c in citations
                        ],
                    )
                )

            analysis.status = RiskAnalysisStatus.COMPLETED
            analysis.risk_score = _compute_risk_score(severities)
            await db.commit()
            logger.info(
                "analyze_document.completed",
                document_id=str(document_id),
                finding_count=len(severities),
                risk_score=analysis.risk_score,
            )
        except Exception as exc:
            await db.rollback()
            analysis = await db.get(RiskAnalysis, analysis.id)
            analysis.status = RiskAnalysisStatus.FAILED
            analysis.error_message = "An unexpected error occurred while analyzing this document."
            await db.commit()
            logger.error("analyze_document.failed", document_id=str(document_id), error=str(exc))


async def start_analysis(
    db: AsyncSession, document_id: uuid.UUID, organization_id: uuid.UUID
) -> RiskAnalysis:
    analysis = RiskAnalysis(
        organization_id=organization_id,
        document_id=document_id,
        status=RiskAnalysisStatus.RUNNING,
        findings=[],
    )
    db.add(analysis)
    await db.commit()
    # Only refresh server-generated column defaults (created_at/updated_at)
    # -- refreshing with no attribute_names would also expire the
    # `findings` relationship, forcing a lazy load outside the request's
    # awaited scope when the response serializer accesses it.
    await db.refresh(analysis, attribute_names=["created_at", "updated_at"])
    return analysis


async def get_latest_analysis(
    db: AsyncSession, document_id: uuid.UUID, organization_id: uuid.UUID
) -> RiskAnalysis:
    stmt = (
        select(RiskAnalysis)
        .options(selectinload(RiskAnalysis.findings))
        .where(RiskAnalysis.document_id == document_id)
        .order_by(RiskAnalysis.created_at.desc())
        .limit(1)
    )
    analysis = (await db.execute(stmt)).scalar_one_or_none()
    if analysis is None:
        raise NotFoundError("No analysis has been run for this document yet.")
    if analysis.organization_id != organization_id:
        raise ForbiddenError("You do not have access to this analysis.")
    return analysis
