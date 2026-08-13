import asyncio

import pytest
from httpx import AsyncClient

from app.services.storage import get_storage_backend

pytestmark = pytest.mark.asyncio

SAMPLE_CONTRACT = b"""MASTER SERVICES AGREEMENT

This agreement is between Acme Corp and Widget LLC.

8.2 Termination

Either party may terminate this agreement upon 7 days written notice to the \
other party if the other party materially breaches this agreement and fails \
to cure such breach within the applicable cure period.

9 Limitation of Liability

Neither party's liability under this agreement shall exceed the total fees \
paid in the twelve months preceding the claim, except for breaches of \
confidentiality obligations set forth in Section 5 of this Agreement.
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


async def _register(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "supersecret1",
            "full_name": "Test User",
            "organization_name": f"Org for {email}",
        },
    )
    return response.json()["access_token"]


async def _upload_and_wait(client: AsyncClient, headers: dict) -> str:
    upload = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("msa.txt", SAMPLE_CONTRACT, "text/plain")},
    )
    document_id = upload.json()["id"]
    for _ in range(20):
        response = await client.get(f"/api/documents/{document_id}", headers=headers)
        if response.json()["status"] in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)
    return document_id


async def test_search_finds_relevant_clause(client: AsyncClient):
    token = await _register(client, "search@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    await _upload_and_wait(client, headers)

    response = await client.post(
        "/api/search", headers=headers, json={"query": "termination notice period"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["chunks"]
    assert body["evidence_score"] > 0
    top_texts = " ".join(c["text"] for c in body["chunks"])
    assert "terminate" in top_texts.lower()


async def test_search_is_scoped_to_organization(client: AsyncClient):
    token_a = await _register(client, "search-org-a@example.com")
    token_b = await _register(client, "search-org-b@example.com")
    await _upload_and_wait(client, {"Authorization": f"Bearer {token_a}"})

    response = await client.post(
        "/api/search",
        headers={"Authorization": f"Bearer {token_b}"},
        json={"query": "termination notice"},
    )
    assert response.status_code == 200
    assert response.json()["chunks"] == []


async def test_search_respects_document_ids_filter(client: AsyncClient):
    token = await _register(client, "search-filter@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    document_id = await _upload_and_wait(client, headers)

    response = await client.post(
        "/api/search",
        headers=headers,
        json={"query": "termination", "document_ids": [document_id]},
    )
    assert response.status_code == 200
    assert all(c["document_id"] == document_id for c in response.json()["chunks"])

    other_id = "00000000-0000-0000-0000-000000000000"
    empty_response = await client.post(
        "/api/search",
        headers=headers,
        json={"query": "termination", "document_ids": [other_id]},
    )
    assert empty_response.json()["chunks"] == []
