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


async def _wait_for_status(client: AsyncClient, headers: dict, document_id: str) -> dict:
    for _ in range(20):
        response = await client.get(f"/api/documents/{document_id}", headers=headers)
        body = response.json()
        if body["status"] in ("completed", "failed"):
            return body
        await asyncio.sleep(0.05)
    raise TimeoutError("Document did not finish processing in time.")


async def test_upload_rejects_unsupported_file_type(client: AsyncClient):
    token = await _register(client, "reject@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("malware.exe", b"binary", "application/x-msdownload")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_upload_and_process_txt_document(client: AsyncClient):
    token = await _register(client, "upload@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("msa.txt", SAMPLE_CONTRACT, "text/plain")},
    )
    assert response.status_code == 200
    document = response.json()
    assert document["status"] in ("processing", "completed")

    final = await _wait_for_status(client, headers, document["id"])
    assert final["status"] == "completed"
    assert final["page_count"] == 1


async def test_documents_are_scoped_to_organization(client: AsyncClient):
    token_a = await _register(client, "org-a@example.com")
    token_b = await _register(client, "org-b@example.com")

    upload = await client.post(
        "/api/documents",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("msa.txt", SAMPLE_CONTRACT, "text/plain")},
    )
    document_id = upload.json()["id"]

    cross_org_response = await client.get(
        f"/api/documents/{document_id}", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert cross_org_response.status_code == 403

    own_org_list = await client.get(
        "/api/documents", headers={"Authorization": f"Bearer {token_a}"}
    )
    assert len(own_org_list.json()["documents"]) == 1

    other_org_list = await client.get(
        "/api/documents", headers={"Authorization": f"Bearer {token_b}"}
    )
    assert other_org_list.json()["documents"] == []


async def test_delete_document_soft_deletes(client: AsyncClient):
    token = await _register(client, "delete@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    upload = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("msa.txt", SAMPLE_CONTRACT, "text/plain")},
    )
    document_id = upload.json()["id"]

    delete_response = await client.delete(f"/api/documents/{document_id}", headers=headers)
    assert delete_response.status_code == 204

    list_response = await client.get("/api/documents", headers=headers)
    assert list_response.json()["documents"] == []

    get_response = await client.get(f"/api/documents/{document_id}", headers=headers)
    assert get_response.status_code == 404
