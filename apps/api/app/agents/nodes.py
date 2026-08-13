import re
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import AgentState
from app.agents.tools import build_tool_registry, call_tool
from app.core.config import get_settings
from app.core.prompts import load_prompt
from app.retrieval.types import RetrievedChunk
from app.services.citations import build_evidence_block, validate_citations
from app.services.llm import LLMMessage, get_llm_provider

settings = get_settings()

ABSTENTION_MESSAGE = (
    "I couldn't determine this from the provided documents.\n\n"
    "The available evidence does not contain enough information to answer this "
    "question reliably."
)

_SECTION_RE = re.compile(r"\b(?:section|clause)\s+(\d+(?:\.\d+)*)\b", re.IGNORECASE)
_COMPARE_WORDS = ("compare", "difference", "versus", " vs ")


def classify_query(state: AgentState) -> dict:
    """Heuristic intent classification. In demo mode (no LLM function-
    calling wired up — see docs/agent.md) this is a keyword classifier;
    swapping in an LLM-based classifier only requires changing this node,
    since it's the only place `intent` is set."""
    query_lower = state["query"].lower()

    if any(word in query_lower for word in _COMPARE_WORDS) and len(state["document_ids"]) >= 2:
        intent = "comparison"
    elif _SECTION_RE.search(query_lower):
        intent = "clause_lookup"
    else:
        intent = "contract_question"

    return {"intent": intent}


def plan(state: AgentState) -> dict:
    """Decides which tool(s) to call based on intent. Recorded as planned
    tool_calls; `retrieve` executes them."""
    planned: list[dict] = [
        {
            "tool": "search_documents",
            "input": {
                "query": state["query"],
                "document_ids": state["document_ids"] or None,
                "top_k": settings.RETRIEVAL_TOP_K,
            },
        }
    ]

    if state["intent"] == "comparison" and len(state["document_ids"]) >= 2:
        match = _SECTION_RE.search(state["query"])
        if match:
            planned.append(
                {
                    "tool": "compare_clauses",
                    "input": {
                        "document_id_a": state["document_ids"][0],
                        "document_id_b": state["document_ids"][1],
                        "section": match.group(1),
                    },
                }
            )

    return {"tool_calls": planned}


def build_retrieve_node(db: AsyncSession, organization_id: uuid.UUID):
    registry = build_tool_registry(db, organization_id)

    async def retrieve(state: AgentState) -> dict:
        executed_calls: list[dict] = []
        retrieved_chunks: list[dict] = []
        errors: list[str] = []

        for planned_call in state["tool_calls"]:
            record = await call_tool(registry, planned_call["tool"], planned_call["input"])
            executed_calls.append(
                {
                    "tool": record.name,
                    "input": record.input,
                    "output": record.output,
                    "latency_ms": record.latency_ms,
                    "error": record.error,
                }
            )
            if record.error:
                errors.append(f"{record.name}: {record.error}")
            elif record.name == "search_documents" and record.output:
                retrieved_chunks = record.output["chunks"]

        return {"tool_calls": executed_calls, "retrieved_chunks": retrieved_chunks, "errors": errors}

    return retrieve


def evaluate_evidence(state: AgentState) -> dict:
    if not state["retrieved_chunks"]:
        return {"evidence_score": 0.0}
    top_score = state["retrieved_chunks"][0].get("rerank_score") or 0.0
    return {"evidence_score": top_score}


def route_on_evidence(state: AgentState) -> str:
    if state["evidence_score"] >= settings.EVIDENCE_THRESHOLD and state["retrieved_chunks"]:
        return "reason"
    return "abstain"


def _to_retrieved_chunks(raw_chunks: list[dict]) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id=uuid.UUID(c["chunk_id"]),
            document_id=uuid.UUID(c["document_id"]),
            filename=c["filename"],
            page=c.get("page"),
            section=c.get("section"),
            heading=c.get("heading"),
            chunk_type="contract_clause",
            text=c["text"],
            rerank_score=c.get("rerank_score"),
        )
        for c in raw_chunks
    ]


async def reason(state: AgentState) -> dict:
    chunks = _to_retrieved_chunks(state["retrieved_chunks"])
    prompt_template = load_prompt("qa", "v1")
    prompt = prompt_template.format(query=state["query"], evidence=build_evidence_block(chunks))

    llm = get_llm_provider()
    response = await llm.complete([LLMMessage(role="user", content=prompt)])
    return {"answer": response.text}


def abstain(state: AgentState) -> dict:
    return {"answer": ABSTENTION_MESSAGE, "citations": []}


def validate_claims(state: AgentState) -> dict:
    """Lightweight faithfulness check: an answer produced on the `reason`
    path should contain at least one citation marker per substantive
    sentence. This doesn't block the response (validate_citations is the
    hard gate) — it records a warning so weakly-supported answers are
    visible in the agent trace instead of looking identical to well-cited
    ones."""
    if state["answer"] is None or state["answer"] == ABSTENTION_MESSAGE:
        return {}

    sentences = [s for s in re.split(r"(?<=[.!?])\s+", state["answer"]) if s.strip()]
    unsupported = [s for s in sentences if not re.search(r"\[\d+\]", s)]

    errors = list(state["errors"])
    if sentences and len(unsupported) == len(sentences):
        errors.append("validate_claims: no sentence in the answer carries a citation marker.")
    return {"errors": errors}


def validate_citations_node(state: AgentState) -> dict:
    if state["answer"] is None or state["answer"] == ABSTENTION_MESSAGE:
        return {"citations": state["citations"]}

    chunks = _to_retrieved_chunks(state["retrieved_chunks"])
    cleaned_answer, citations = validate_citations(state["answer"], chunks)

    if not citations:
        # Generation produced no evidence-backed claim -- abstain rather
        # than show unsupported text, mirroring the pre-generation gate.
        return {"answer": ABSTENTION_MESSAGE, "citations": []}

    return {
        "answer": cleaned_answer,
        "citations": [
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
    }


def final_response(state: AgentState) -> dict:
    confidence = state["evidence_score"] if state["citations"] else 0.0
    return {"confidence": confidence}
