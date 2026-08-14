import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agents import build_agent_graph
from app.agents.state import AgentState
from app.core.errors import ForbiddenError, NotFoundError
from app.core.logging import get_logger
from app.models.agent_run import AgentRun, AgentRunStatus
from app.models.agent_step import AgentStep
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.observability import AgentTrace, TraceStep, get_observability_client
from app.services.cost import estimate_cost

logger = get_logger("agent_service")


def _initial_state(query: str, organization_id: uuid.UUID, document_ids: list[str]) -> AgentState:
    return {
        "query": query,
        "organization_id": str(organization_id),
        "document_ids": document_ids,
        "intent": "",
        "retrieved_chunks": [],
        "evidence_score": 0.0,
        "answer": None,
        "citations": [],
        "confidence": 0.0,
        "tool_calls": [],
        "errors": [],
        "model": "",
        "input_tokens": 0,
        "output_tokens": 0,
    }


def _state_snapshot(state: AgentState) -> dict:
    """A trimmed view of state for a step's recorded "input" — the full
    state (especially retrieved chunk text) is already visible on the
    steps that produced it, so this avoids repeating large blobs on every
    subsequent step."""
    return {
        "query": state["query"],
        "intent": state["intent"],
        "evidence_score": state["evidence_score"],
        "retrieved_chunk_count": len(state["retrieved_chunks"]),
        "confidence": state["confidence"],
    }


async def get_or_create_conversation(
    db: AsyncSession,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    conversation_id: uuid.UUID | None,
    title_hint: str,
) -> Conversation:
    if conversation_id is not None:
        conversation = await db.get(Conversation, conversation_id)
        if conversation is None or conversation.organization_id != organization_id:
            raise NotFoundError("Conversation not found.")
        return conversation

    conversation = Conversation(
        organization_id=organization_id,
        user_id=user_id,
        title=title_hint[:255],
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def stream_agent(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    query: str,
    document_ids: list[str],
    conversation_id: uuid.UUID | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """Runs the LangGraph agent, yielding one event per completed node so
    the caller (the SSE endpoint) can stream live progress — the same
    granularity the Agent Runs trace UI shows after the fact. Persists an
    AgentRun + one AgentStep per node + the user/assistant Message pair,
    exactly as a non-streaming run would."""
    conversation = await get_or_create_conversation(
        db, organization_id, user_id, conversation_id, title_hint=query
    )

    agent_run = AgentRun(
        organization_id=organization_id,
        user_id=user_id,
        conversation_id=conversation.id,
        query=query,
        status=AgentRunStatus.RUNNING,
    )
    db.add(agent_run)
    await db.flush()

    db.add(Message(conversation_id=conversation.id, role=MessageRole.USER, content=query))

    yield {"type": "run_started", "agent_run_id": str(agent_run.id), "conversation_id": str(conversation.id)}

    graph = build_agent_graph(db, organization_id)
    state = _initial_state(query, organization_id, document_ids)

    step_index = 0
    total_start = time.perf_counter()
    step_start = total_start
    trace_steps: list[TraceStep] = []

    try:
        async for update in graph.astream(state, stream_mode="updates"):
            for node_name, partial in update.items():
                now = time.perf_counter()
                latency_ms = (now - step_start) * 1000
                step = AgentStep(
                    agent_run_id=agent_run.id,
                    step_index=step_index,
                    step_name=node_name,
                    input=_state_snapshot(state),
                    output=partial,
                    latency_ms=latency_ms,
                )
                db.add(step)
                trace_steps.append(
                    TraceStep(
                        name=node_name,
                        input=_state_snapshot(state),
                        output=partial,
                        latency_ms=latency_ms,
                    )
                )
                yield {
                    "type": "step",
                    "step_index": step_index,
                    "step_name": node_name,
                    "output": partial,
                    "latency_ms": latency_ms,
                }
                step_index += 1
                step_start = now
                state = {**state, **partial}
    except Exception as exc:
        agent_run.status = AgentRunStatus.FAILED
        agent_run.error_message = "The agent encountered an unexpected error."
        agent_run.latency_ms = (time.perf_counter() - total_start) * 1000
        await db.commit()
        logger.error("agent_run.failed", agent_run_id=str(agent_run.id), error=str(exc))
        yield {"type": "error", "message": "The agent encountered an unexpected error."}
        return

    agent_run.status = AgentRunStatus.COMPLETED
    agent_run.intent = state["intent"]
    agent_run.answer = state["answer"]
    agent_run.citations = state["citations"]
    agent_run.evidence_score = state["evidence_score"]
    agent_run.confidence = state["confidence"]
    agent_run.latency_ms = (time.perf_counter() - total_start) * 1000
    agent_run.model = state["model"] or None
    agent_run.prompt_version = "v1" if state["model"] else None
    agent_run.input_tokens = state["input_tokens"]
    agent_run.output_tokens = state["output_tokens"]
    agent_run.estimated_cost_usd = (
        estimate_cost(state["model"], state["input_tokens"], state["output_tokens"])
        if state["model"]
        else 0.0
    )

    db.add(
        Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content=state["answer"] or "",
            citations=state["citations"],
        )
    )
    await db.commit()

    get_observability_client().record_agent_trace(
        AgentTrace(
            trace_id=str(agent_run.id),
            organization_id=str(organization_id),
            query=query,
            intent=state["intent"],
            answer=state["answer"],
            model=agent_run.model,
            prompt_version=agent_run.prompt_version,
            evidence_score=state["evidence_score"],
            confidence=state["confidence"],
            input_tokens=state["input_tokens"],
            output_tokens=state["output_tokens"],
            estimated_cost_usd=agent_run.estimated_cost_usd or 0.0,
            latency_ms=agent_run.latency_ms or 0.0,
            steps=trace_steps,
            errors=state["errors"],
        )
    )

    yield {
        "type": "done",
        "agent_run_id": str(agent_run.id),
        "conversation_id": str(conversation.id),
        "answer": state["answer"],
        "citations": state["citations"],
        "confidence": state["confidence"],
        "evidence_score": state["evidence_score"],
        "intent": state["intent"],
    }


async def run_agent(
    db: AsyncSession,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    query: str,
    document_ids: list[str],
    conversation_id: uuid.UUID | None = None,
) -> tuple[AgentRun, Conversation]:
    """Non-streaming convenience wrapper over stream_agent for callers
    (tests, background jobs) that just want the final result."""
    agent_run_id: uuid.UUID | None = None
    async for event in stream_agent(
        db,
        organization_id=organization_id,
        user_id=user_id,
        query=query,
        document_ids=document_ids,
        conversation_id=conversation_id,
    ):
        if event["type"] in ("run_started", "done"):
            agent_run_id = uuid.UUID(event["agent_run_id"])

    assert agent_run_id is not None
    agent_run = await get_agent_run(db, agent_run_id, organization_id)
    conversation = await get_conversation(db, agent_run.conversation_id, organization_id)
    return agent_run, conversation


async def get_agent_run(
    db: AsyncSession, agent_run_id: uuid.UUID, organization_id: uuid.UUID
) -> AgentRun:
    stmt = (
        select(AgentRun).options(selectinload(AgentRun.steps)).where(AgentRun.id == agent_run_id)
    )
    agent_run = (await db.execute(stmt)).scalar_one_or_none()
    if agent_run is None:
        raise NotFoundError("Agent run not found.")
    if agent_run.organization_id != organization_id:
        raise ForbiddenError("You do not have access to this agent run.")
    return agent_run


async def list_agent_runs(
    db: AsyncSession, organization_id: uuid.UUID, limit: int = 50
) -> list[AgentRun]:
    stmt = (
        select(AgentRun)
        .where(AgentRun.organization_id == organization_id)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_conversations(
    db: AsyncSession, organization_id: uuid.UUID, user_id: uuid.UUID
) -> list[Conversation]:
    stmt = (
        select(Conversation)
        .where(Conversation.organization_id == organization_id, Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def get_conversation(
    db: AsyncSession, conversation_id: uuid.UUID, organization_id: uuid.UUID
) -> Conversation:
    stmt = (
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conversation_id)
    )
    conversation = (await db.execute(stmt)).scalar_one_or_none()
    if conversation is None:
        raise NotFoundError("Conversation not found.")
    if conversation.organization_id != organization_id:
        raise ForbiddenError("You do not have access to this conversation.")
    return conversation
