import asyncio
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.agents import build_agent_graph
from app.models.user import User
from app.services.storage import get_storage_backend

pytestmark = pytest.mark.asyncio

SAMPLE_CONTRACT = b"""MASTER SERVICES AGREEMENT

This agreement is between Acme Corp and Widget LLC.

8.2 Termination

Either party may terminate this agreement upon 7 days written notice to the \
other party if the other party materially breaches this agreement and fails \
to cure such breach within the applicable cure period.
"""


@pytest.fixture(autouse=True)
def _reset_storage_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.services.storage.get_settings",
        lambda: type(
            "S", (), {"STORAGE_BACKEND": "local", "STORAGE_LOCAL_PATH": str(tmp_path)}
        )(),
    )
    get_storage_backend.cache_clear()
    yield
    get_storage_backend.cache_clear()


async def _register_and_upload(client: AsyncClient, db_session, email: str) -> uuid.UUID:
    register = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "supersecret1",
            "full_name": "Test User",
            "organization_name": f"Org for {email}",
        },
    )
    token = register.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("msa.txt", SAMPLE_CONTRACT, "text/plain")},
    )
    document_id = upload.json()["id"]
    for _ in range(20):
        status = (
            await client.get(f"/api/documents/{document_id}", headers=headers)
        ).json()["status"]
        if status in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)

    user = (await db_session.execute(select(User).where(User.email == email))).scalar_one()
    return user.organization_id


def _initial_state(query: str, document_ids: list[str] | None = None) -> dict:
    return {
        "query": query,
        "organization_id": "",
        "document_ids": document_ids or [],
        "intent": "",
        "retrieved_chunks": [],
        "evidence_score": 0.0,
        "answer": None,
        "citations": [],
        "confidence": 0.0,
        "tool_calls": [],
        "errors": [],
    }


async def test_graph_answers_grounded_question_with_citations(client: AsyncClient, db_session):
    org_id = await _register_and_upload(client, db_session, "graph-answer@example.com")
    graph = build_agent_graph(db_session, org_id)

    final_state = await graph.ainvoke(
        _initial_state("What is the written notice period required to terminate?")
    )

    assert final_state["intent"] == "contract_question"
    assert final_state["evidence_score"] > 0
    assert final_state["citations"]
    assert "[1]" in final_state["answer"]
    assert final_state["confidence"] > 0
    assert not final_state["errors"]


async def test_graph_abstains_on_insufficient_evidence(client: AsyncClient, db_session):
    org_id = await _register_and_upload(client, db_session, "graph-abstain@example.com")
    graph = build_agent_graph(db_session, org_id)

    final_state = await graph.ainvoke(
        _initial_state("What is the maximum penalty for late spacecraft delivery?")
    )

    assert "couldn't determine" in final_state["answer"].lower()
    assert final_state["citations"] == []
    assert final_state["confidence"] == 0.0


async def test_graph_classifies_clause_lookup_intent(client: AsyncClient, db_session):
    org_id = await _register_and_upload(client, db_session, "graph-clause@example.com")
    graph = build_agent_graph(db_session, org_id)

    final_state = await graph.ainvoke(_initial_state("What does section 8.2 say?"))

    assert final_state["intent"] == "clause_lookup"


async def test_graph_records_tool_calls(client: AsyncClient, db_session):
    org_id = await _register_and_upload(client, db_session, "graph-tools@example.com")
    graph = build_agent_graph(db_session, org_id)

    final_state = await graph.ainvoke(_initial_state("What are the termination terms?"))

    assert final_state["tool_calls"]
    assert final_state["tool_calls"][0]["tool"] == "search_documents"
    assert final_state["tool_calls"][0]["error"] is None
