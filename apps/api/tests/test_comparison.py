import asyncio

import pytest
from httpx import AsyncClient

from app.services.storage import get_storage_backend

pytestmark = pytest.mark.asyncio

CONTRACT_A = b"""MASTER SERVICES AGREEMENT A

8.2 Termination

Either party may terminate this agreement upon 30 days written notice to the other party.

9 Limitation of Liability

Liability under this agreement shall be capped at the total fees paid in the prior year.
"""

CONTRACT_B = b"""MASTER SERVICES AGREEMENT B

8.2 Termination

Either party may terminate this agreement immediately upon 7 days written notice.

9 Limitation of Liability

Liability under this agreement shall be unlimited and uncapped for all claims.
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


async def _upload(client: AsyncClient, headers: dict, filename: str, content: bytes) -> str:
    upload = await client.post(
        "/api/documents", headers=headers, files={"file": (filename, content, "text/plain")}
    )
    document_id = upload.json()["id"]
    for _ in range(20):
        status = (
            await client.get(f"/api/documents/{document_id}", headers=headers)
        ).json()["status"]
        if status in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)
    return document_id


async def _register(client: AsyncClient, email: str) -> dict:
    register = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "supersecret1",
            "full_name": "Test User",
            "organization_name": f"Org for {email}",
        },
    )
    return {"Authorization": f"Bearer {register.json()['access_token']}"}


async def test_compare_documents_returns_both_sides_with_citations(client: AsyncClient):
    headers = await _register(client, "compare@example.com")
    doc_a = await _upload(client, headers, "contract_a.txt", CONTRACT_A)
    doc_b = await _upload(client, headers, "contract_b.txt", CONTRACT_B)

    response = await client.post(
        "/api/comparisons",
        headers=headers,
        json={"document_id_a": doc_a, "document_id_b": doc_b},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert rows

    liability_row = next(r for r in rows if r["category"] == "liability")
    assert liability_row["document_a"]["found"] is True
    assert liability_row["document_b"]["found"] is True
    assert "capped" in liability_row["document_a"]["text"].lower()
    assert "unlimited" in liability_row["document_b"]["text"].lower()
    assert liability_row["document_a"]["chunk_id"] is not None


async def test_compare_rejects_same_document(client: AsyncClient):
    headers = await _register(client, "compare-same@example.com")
    doc_a = await _upload(client, headers, "contract_a.txt", CONTRACT_A)

    response = await client.post(
        "/api/comparisons",
        headers=headers,
        json={"document_id_a": doc_a, "document_id_b": doc_a},
    )
    assert response.status_code == 422


async def test_compare_is_scoped_to_organization(client: AsyncClient):
    headers_a = await _register(client, "compare-org-a@example.com")
    doc_a = await _upload(client, headers_a, "contract_a.txt", CONTRACT_A)
    doc_b = await _upload(client, headers_a, "contract_b.txt", CONTRACT_B)

    headers_c = await _register(client, "compare-org-c@example.com")
    response = await client.post(
        "/api/comparisons",
        headers=headers_c,
        json={"document_id_a": doc_a, "document_id_b": doc_b},
    )
    assert response.status_code in (403, 404)
