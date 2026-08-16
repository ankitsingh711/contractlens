import uuid

import pytest
from httpx import AsyncClient

from app.core.config import get_settings

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def _lower_rate_limit(monkeypatch):
    # The real default (60/min) would need 61 real requests to trip in a
    # test; lower it so a handful of requests is enough to exercise the
    # limiter. get_settings() is an lru_cached singleton reused by both the
    # app and the middleware, so mutating the instance in place affects
    # every caller without needing to patch each import site separately.
    monkeypatch.setattr(get_settings(), "RATE_LIMIT_PER_MINUTE", 3)


@pytest.fixture
def fake_ip() -> str:
    # A unique-per-test fake IP (sent via X-Forwarded-For) keeps each
    # test's rate-limit counters isolated from every other test, even when
    # tests run back-to-back within the same fixed window.
    return f"203.0.113.{uuid.uuid4().int % 250 + 1}"


async def _register(client: AsyncClient, email: str) -> dict:
    response = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "supersecret1",
            "full_name": "Test User",
            "organization_name": f"Org for {email}",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_requests_under_limit_succeed(client: AsyncClient, fake_ip: str):
    headers = {"X-Forwarded-For": fake_ip}
    for _ in range(3):
        response = await client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "wrong-password"},
            headers=headers,
        )
        # Under the limit: the request is processed normally (rejected for
        # bad credentials, not for rate limiting).
        assert response.status_code == 401


async def test_exceeding_limit_returns_429_with_retry_after(client: AsyncClient, fake_ip: str):
    headers = {"X-Forwarded-For": fake_ip}
    statuses = []
    for _ in range(5):
        response = await client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "wrong-password"},
            headers=headers,
        )
        statuses.append(response.status_code)

    assert statuses[:3] == [401, 401, 401]
    assert statuses[3:] == [429, 429]

    body = response.json()
    assert body["error"]["code"] == "RATE_LIMITED"
    assert "request_id" in body["error"]
    assert "Retry-After" in response.headers
    retry_after = int(response.headers["Retry-After"])
    assert 0 < retry_after <= 60


async def test_different_identifiers_have_independent_limits(client: AsyncClient):
    ip_a = {"X-Forwarded-For": "198.51.100.10"}
    ip_b = {"X-Forwarded-For": "198.51.100.20"}

    # Exhaust the budget for IP A.
    for _ in range(3):
        response = await client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "wrong-password"},
            headers=ip_a,
        )
        assert response.status_code == 401
    blocked = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password"},
        headers=ip_a,
    )
    assert blocked.status_code == 429

    # IP B has its own independent budget and is unaffected.
    allowed = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password"},
        headers=ip_b,
    )
    assert allowed.status_code == 401


async def test_authenticated_requests_are_scoped_per_user(client: AsyncClient):
    # Registration is unauthenticated (no bearer token yet), so it is
    # counted against the caller's IP bucket, not a per-user bucket.
    headers_a = await _register(client, f"user-a-{uuid.uuid4().hex[:8]}@example.com")
    headers_b = await _register(client, f"user-b-{uuid.uuid4().hex[:8]}@example.com")

    # GET requests are exempt, so these never touch either budget.
    for _ in range(5):
        response = await client.get("/api/auth/me", headers=headers_a)
        assert response.status_code == 200

    # POST /api/auth/login while authenticated is identified by the bearer
    # token (not IP), since resolve_identifier checks for a valid token
    # first regardless of which endpoint is hit. Exhaust user A's budget.
    for _ in range(3):
        response = await client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "wrong-password"},
            headers=headers_a,
        )
        assert response.status_code == 401

    blocked = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password"},
        headers=headers_a,
    )
    assert blocked.status_code == 429

    # User B's own budget is untouched by user A's activity.
    response = await client.post(
        "/api/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-password"},
        headers=headers_b,
    )
    assert response.status_code == 401


async def test_health_endpoint_is_never_rate_limited(client: AsyncClient, fake_ip: str):
    headers = {"X-Forwarded-For": fake_ip}
    for _ in range(10):
        response = await client.get("/api/health", headers=headers)
        assert response.status_code == 200


async def test_get_requests_are_not_rate_limited(client: AsyncClient):
    headers = await _register(client, f"reader-{uuid.uuid4().hex[:8]}@example.com")
    # GET requests are exempt from the budget (see RATE_LIMIT_SAFE_METHODS
    # in app/core/middleware.py) so polling-heavy endpoints like this one
    # are unaffected even with a very low limit configured.
    for _ in range(10):
        response = await client.get("/api/auth/me", headers=headers)
        assert response.status_code == 200
