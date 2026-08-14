import asyncio

import pytest
from httpx import AsyncClient

from app.services.storage import get_storage_backend

pytestmark = pytest.mark.asyncio

SAMPLE_CONTRACT = b"""MASTER SERVICES AGREEMENT

This agreement is between Acme Corp and Widget LLC.

8.2 Termination

Either party may terminate this agreement immediately and at its sole discretion, \
without cause and without notice, upon written communication to the other party.

9 Limitation of Liability

Neither party shall have any limitation on liability for damages arising under this \
agreement, and liability shall be unlimited and uncapped for all claims.

10 Confidentiality

Each party shall keep the other party's confidential information confidential for the \
term of this agreement, subject to standard exceptions for legally compelled disclosure.
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


async def _register_and_upload(client: AsyncClient, email: str, contract: bytes = SAMPLE_CONTRACT) -> tuple[dict, str]:
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
        files={"file": ("msa.txt", contract, "text/plain")},
    )
    document_id = upload.json()["id"]
    for _ in range(20):
        status = (
            await client.get(f"/api/documents/{document_id}", headers=headers)
        ).json()["status"]
        if status in ("completed", "failed"):
            break
        await asyncio.sleep(0.05)
    return headers, document_id


async def _wait_for_analysis(client: AsyncClient, headers: dict, document_id: str) -> dict:
    for _ in range(30):
        response = await client.get(f"/api/documents/{document_id}/analysis", headers=headers)
        body = response.json()
        if body["status"] in ("completed", "failed"):
            return body
        await asyncio.sleep(0.05)
    raise TimeoutError("Analysis did not finish in time.")


async def test_analyze_document_produces_evidence_backed_findings(client: AsyncClient):
    headers, document_id = await _register_and_upload(client, "risk-analyze@example.com")

    trigger = await client.post(f"/api/documents/{document_id}/analyze", headers=headers)
    assert trigger.status_code == 200
    assert trigger.json()["status"] == "running"

    analysis = await _wait_for_analysis(client, headers, document_id)
    assert analysis["status"] == "completed"
    assert analysis["risk_score"] is not None
    assert 0 <= analysis["risk_score"] <= 100
    assert analysis["findings"]

    for finding in analysis["findings"]:
        assert finding["citations"], f"finding {finding['category']} has no citations"
        assert finding["severity"] in ("high", "medium", "low")


async def test_analyze_document_flags_unlimited_liability_as_high_severity(client: AsyncClient):
    headers, document_id = await _register_and_upload(client, "risk-liability@example.com")
    await client.post(f"/api/documents/{document_id}/analyze", headers=headers)
    analysis = await _wait_for_analysis(client, headers, document_id)

    liability_findings = [f for f in analysis["findings"] if f["category"] == "liability"]
    assert liability_findings
    assert liability_findings[0]["severity"] == "high"


async def test_analyze_document_does_not_fabricate_categories_with_no_evidence(client: AsyncClient):
    minimal_contract = b"This is a short document about pricing.\n\n1 Fees\n\nThe fee is $100 per month."
    headers, document_id = await _register_and_upload(
        client, "risk-minimal@example.com", contract=minimal_contract
    )
    await client.post(f"/api/documents/{document_id}/analyze", headers=headers)
    analysis = await _wait_for_analysis(client, headers, document_id)

    categories_found = {f["category"] for f in analysis["findings"]}
    # A document with no indemnification/data-protection language should
    # not produce fabricated findings for those categories.
    assert "indemnification" not in categories_found
    assert "data_protection" not in categories_found


async def test_analysis_endpoint_scoped_to_organization(client: AsyncClient):
    headers_a, document_id = await _register_and_upload(client, "risk-org-a@example.com")
    register_b = await client.post(
        "/api/auth/register",
        json={
            "email": "risk-org-b@example.com",
            "password": "supersecret1",
            "full_name": "User B",
            "organization_name": "Org B",
        },
    )
    headers_b = {"Authorization": f"Bearer {register_b.json()['access_token']}"}

    cross_org = await client.post(f"/api/documents/{document_id}/analyze", headers=headers_b)
    assert cross_org.status_code == 403

    cross_org_get = await client.get(f"/api/documents/{document_id}/analysis", headers=headers_b)
    assert cross_org_get.status_code in (403, 404)


async def test_get_analysis_before_any_run_returns_404(client: AsyncClient):
    headers, document_id = await _register_and_upload(client, "risk-none@example.com")
    response = await client.get(f"/api/documents/{document_id}/analysis", headers=headers)
    assert response.status_code == 404
