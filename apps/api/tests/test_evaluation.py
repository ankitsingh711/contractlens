import asyncio
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.services.storage import get_storage_backend

pytestmark = pytest.mark.asyncio

SEED_DIR = Path(__file__).resolve().parents[3] / "evaluation" / "seed_documents"
SEED_FILES = [
    "master_services_agreement.txt",
    "non_disclosure_agreement.txt",
    "data_processing_agreement.txt",
    "software_license_agreement.txt",
]


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


async def _upload_seed_documents(client: AsyncClient, headers: dict) -> None:
    for filename in SEED_FILES:
        content = (SEED_DIR / filename).read_bytes()
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
        assert status == "completed", f"seed document failed to process: {filename}"


async def _wait_for_evaluation(client: AsyncClient, headers: dict, run_id: str) -> dict:
    for _ in range(120):
        response = await client.get(f"/api/evaluations/{run_id}", headers=headers)
        body = response.json()
        if body["status"] in ("completed", "failed"):
            return body
        await asyncio.sleep(0.1)
    raise TimeoutError("Evaluation did not finish in time.")


async def test_evaluation_run_scores_the_full_dataset(client: AsyncClient):
    headers = await _register(client, "eval@example.com")
    await _upload_seed_documents(client, headers)

    trigger = await client.post("/api/evaluations/run", headers=headers)
    assert trigger.status_code == 200
    run_id = trigger.json()["id"]

    run = await _wait_for_evaluation(client, headers, run_id)
    assert run["status"] == "completed"
    assert run["total_cases"] == 52
    assert run["passed_cases"] + run["failed_cases"] == 52
    assert run["passed_cases"] > 30  # most cases should pass against the real seed docs

    for metric in [
        "faithfulness",
        "citation_accuracy",
        "retrieval_recall",
        "retrieval_precision",
        "hallucination_rate",
        "answer_relevance",
    ]:
        assert run[metric] is not None
        assert 0.0 <= run[metric] <= 1.0

    assert run["avg_latency_ms"] > 0
    assert run["avg_cost_usd"] == 0.0  # mock provider

    detail = await client.get(f"/api/evaluations/{run_id}", headers=headers)
    results = detail.json()["results"]
    assert len(results) == 52
    assert {r["case_id"] for r in results} == {
        r["case_id"] for r in results
    }  # sanity: ids present
    abstain_result = next(r for r in results if r["case_id"] == "abstain_001")
    assert abstain_result["should_abstain"] is True
    assert abstain_result["abstained"] is True
    assert abstain_result["passed"] is True


async def test_second_evaluation_run_detects_baseline_with_no_regression(client: AsyncClient):
    headers = await _register(client, "eval-regression@example.com")
    await _upload_seed_documents(client, headers)

    first_trigger = await client.post("/api/evaluations/run", headers=headers)
    first_run = await _wait_for_evaluation(client, headers, first_trigger.json()["id"])
    assert first_run["status"] == "completed"

    second_trigger = await client.post("/api/evaluations/run", headers=headers)
    second_run = await _wait_for_evaluation(client, headers, second_trigger.json()["id"])

    assert second_run["baseline_run_id"] == first_run["id"]
    # Same deterministic mock pipeline run twice against the same corpus
    # should produce identical metrics -> no regression.
    assert second_run["regressions"] == []

    list_response = await client.get("/api/evaluations", headers=headers)
    assert len(list_response.json()["evaluation_runs"]) == 2


async def test_evaluation_handles_missing_documents_gracefully(client: AsyncClient):
    headers = await _register(client, "eval-nodoc@example.com")
    # No documents uploaded at all.

    trigger = await client.post("/api/evaluations/run", headers=headers)
    run = await _wait_for_evaluation(client, headers, trigger.json()["id"])

    assert run["status"] == "completed"
    assert run["total_cases"] == 52
    assert run["passed_cases"] == 0
    assert run["failed_cases"] == 52


async def test_evaluation_run_is_scoped_to_organization(client: AsyncClient):
    headers_a = await _register(client, "eval-org-a@example.com")
    trigger = await client.post("/api/evaluations/run", headers=headers_a)
    run_id = trigger.json()["id"]

    headers_b = await _register(client, "eval-org-b@example.com")
    cross_org = await client.get(f"/api/evaluations/{run_id}", headers=headers_b)
    assert cross_org.status_code == 403
