import asyncio
import json

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


async def _register_and_upload(client: AsyncClient, email: str) -> dict:
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
    return headers


def _parse_sse_events(raw_body: str) -> list[dict]:
    events = []
    for chunk in raw_body.split("\n\n"):
        chunk = chunk.strip()
        if chunk.startswith("data: "):
            events.append(json.loads(chunk[len("data: ") :]))
    return events


async def test_chat_streams_agent_steps_and_final_answer(client: AsyncClient):
    headers = await _register_and_upload(client, "chat@example.com")

    async with client.stream(
        "POST",
        "/api/chat",
        headers=headers,
        json={"message": "What is the written notice period required to terminate?"},
    ) as response:
        assert response.status_code == 200
        body = ""
        async for chunk in response.aiter_text():
            body += chunk

    events = _parse_sse_events(body)
    event_types = [e["type"] for e in events]
    assert event_types[0] == "run_started"
    assert "step" in event_types
    assert event_types[-1] == "done"

    done_event = events[-1]
    assert done_event["citations"]
    assert "[1]" in done_event["answer"]

    step_names = [e["step_name"] for e in events if e["type"] == "step"]
    assert "classify_query" in step_names
    assert "retrieve" in step_names
    assert "validate_citations" in step_names


async def test_chat_persists_conversation_and_messages(client: AsyncClient):
    headers = await _register_and_upload(client, "chat-persist@example.com")

    async with client.stream(
        "POST", "/api/chat", headers=headers, json={"message": "What are the termination terms?"}
    ) as response:
        body = ""
        async for chunk in response.aiter_text():
            body += chunk

    done_event = _parse_sse_events(body)[-1]
    conversation_id = done_event["conversation_id"]

    conv_response = await client.get(f"/api/conversations/{conversation_id}", headers=headers)
    assert conv_response.status_code == 200
    messages = conv_response.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"

    list_response = await client.get("/api/conversations", headers=headers)
    assert len(list_response.json()["conversations"]) == 1


async def test_chat_creates_agent_run_with_steps(client: AsyncClient):
    headers = await _register_and_upload(client, "chat-agentrun@example.com")

    async with client.stream(
        "POST", "/api/chat", headers=headers, json={"message": "What are the termination terms?"}
    ) as response:
        body = ""
        async for chunk in response.aiter_text():
            body += chunk

    done_event = _parse_sse_events(body)[-1]
    agent_run_id = done_event["agent_run_id"]

    detail = await client.get(f"/api/agent-runs/{agent_run_id}", headers=headers)
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["status"] == "completed"
    assert len(payload["steps"]) >= 8
    step_indices = [s["step_index"] for s in payload["steps"]]
    assert step_indices == sorted(step_indices)
    assert payload["steps"][0]["step_index"] == 0
    assert payload["steps"][0]["step_name"] == "classify_query"

    list_response = await client.get("/api/agent-runs", headers=headers)
    assert len(list_response.json()["agent_runs"]) == 1


async def test_agent_run_is_scoped_to_organization(client: AsyncClient):
    headers_a = await _register_and_upload(client, "agentrun-org-a@example.com")
    register_b = await client.post(
        "/api/auth/register",
        json={
            "email": "agentrun-org-b@example.com",
            "password": "supersecret1",
            "full_name": "User B",
            "organization_name": "Org B",
        },
    )
    headers_b = {"Authorization": f"Bearer {register_b.json()['access_token']}"}

    async with client.stream(
        "POST", "/api/chat", headers=headers_a, json={"message": "What are the termination terms?"}
    ) as response:
        body = ""
        async for chunk in response.aiter_text():
            body += chunk
    agent_run_id = _parse_sse_events(body)[-1]["agent_run_id"]

    cross_org = await client.get(f"/api/agent-runs/{agent_run_id}", headers=headers_b)
    assert cross_org.status_code == 403
