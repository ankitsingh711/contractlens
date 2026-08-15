import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.user import User, UserRole
from app.services.storage import get_storage_backend

pytestmark = pytest.mark.asyncio

SAMPLE_CONTRACT = b"""MASTER SERVICES AGREEMENT

8.2 Termination

Either party may terminate this agreement upon 7 days written notice.
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


async def test_register_and_login_are_audited(client: AsyncClient):
    headers = await _register(client, "audit-auth@example.com")

    # A registered admin can already see the audit log for their own org.
    logs = (await client.get("/api/audit-logs", headers=headers)).json()["audit_logs"]
    actions = [entry["action"] for entry in logs]
    assert "user.register" in actions

    await client.post(
        "/api/auth/login",
        json={"email": "audit-auth@example.com", "password": "supersecret1"},
    )
    logs = (await client.get("/api/audit-logs", headers=headers)).json()["audit_logs"]
    assert "user.login" in [entry["action"] for entry in logs]


async def test_failed_login_is_audited(client: AsyncClient):
    headers = await _register(client, "audit-failed-login@example.com")

    response = await client.post(
        "/api/auth/login",
        json={"email": "audit-failed-login@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401

    logs = (await client.get("/api/audit-logs", headers=headers)).json()["audit_logs"]
    assert "user.login_failed" in [entry["action"] for entry in logs]


async def test_document_upload_and_delete_are_audited(client: AsyncClient):
    headers = await _register(client, "audit-docs@example.com")

    upload = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("msa.txt", SAMPLE_CONTRACT, "text/plain")},
    )
    document_id = upload.json()["id"]
    await client.delete(f"/api/documents/{document_id}", headers=headers)

    logs = (await client.get("/api/audit-logs", headers=headers)).json()["audit_logs"]
    actions = [entry["action"] for entry in logs]
    assert "document.upload" in actions
    assert "document.delete" in actions

    upload_entry = next(e for e in logs if e["action"] == "document.upload")
    assert upload_entry["resource_id"] == document_id
    assert upload_entry["metadata"]["filename"] == "msa.txt"
    assert upload_entry["user_email"] == "audit-docs@example.com"


async def test_document_analyze_is_audited(client: AsyncClient):
    headers = await _register(client, "audit-analyze@example.com")
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

    await client.post(f"/api/documents/{document_id}/analyze", headers=headers)

    logs = (await client.get("/api/audit-logs", headers=headers)).json()["audit_logs"]
    assert "document.analyze" in [entry["action"] for entry in logs]


async def test_audit_log_requires_admin_role(client: AsyncClient, db_session):
    headers = await _register(client, "audit-member@example.com")

    user = (
        await db_session.execute(
            select(User).where(User.email == "audit-member@example.com")
        )
    ).scalar_one()
    user.role = UserRole.MEMBER
    await db_session.commit()

    response = await client.get("/api/audit-logs", headers=headers)
    assert response.status_code == 403


async def test_audit_log_is_scoped_to_organization(client: AsyncClient):
    headers_a = await _register(client, "audit-org-a@example.com")
    headers_b = await _register(client, "audit-org-b@example.com")

    logs_b = (await client.get("/api/audit-logs", headers=headers_b)).json()["audit_logs"]
    org_a_emails = {e["user_email"] for e in logs_b}
    assert "audit-org-a@example.com" not in org_a_emails

    cross_org = await client.get("/api/audit-logs", headers=headers_a)
    assert cross_org.status_code == 200  # org A admin sees only org A's own entries
    assert all(
        e["user_email"] in (None, "audit-org-a@example.com")
        for e in cross_org.json()["audit_logs"]
    )
