import asyncio
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User
from app.services.rag_service import answer_query
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


async def test_answer_query_returns_grounded_answer_with_citations(client: AsyncClient, db_session):
    org_id = await _register_and_upload(client, db_session, "rag-answer@example.com")

    # Phrased to lexically match the clause body (not just the "8.2
    # Termination" heading chunk) since the mock reranker scores on exact
    # token overlap, not semantics.
    result = await answer_query(
        db_session, "What is the written notice period required to terminate?", org_id
    )

    assert result.abstained is False
    assert result.citations
    assert "[1]" in result.answer
    assert result.citations[0].section == "8.2"
    assert "7 days" in result.citations[0].quote.lower()


async def test_answer_query_abstains_when_no_evidence(client: AsyncClient, db_session):
    org_id = await _register_and_upload(client, db_session, "rag-abstain@example.com")

    result = await answer_query(
        db_session, "What is the maximum penalty for late spacecraft delivery?", org_id
    )

    assert result.abstained is True
    assert "couldn't determine" in result.answer.lower()
    assert result.citations == []


async def test_answer_query_abstains_for_organization_with_no_documents(client: AsyncClient, db_session):
    register = await client.post(
        "/api/auth/register",
        json={
            "email": "rag-empty@example.com",
            "password": "supersecret1",
            "full_name": "Empty Org User",
            "organization_name": "Empty Org",
        },
    )
    token = register.json()["access_token"]
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    org_id = me.json()["organization_id"]

    result = await answer_query(db_session, "What are the termination terms?", org_id)

    assert result.abstained is True
    assert result.retrieved_chunks == []
