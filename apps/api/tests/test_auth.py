import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def test_register_creates_org_and_returns_token(client: AsyncClient):
    response = await client.post(
        "/api/auth/register",
        json={
            "email": "counsel@example.com",
            "password": "supersecret1",
            "full_name": "Jordan Counsel",
            "organization_name": "Example Legal",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


async def test_register_duplicate_email_rejected(client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "password": "supersecret1",
        "full_name": "Dup User",
        "organization_name": "Dup Org",
    }
    first = await client.post("/api/auth/register", json=payload)
    assert first.status_code == 200

    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 422
    assert second.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_login_with_wrong_password_returns_401(client: AsyncClient):
    await client.post(
        "/api/auth/register",
        json={
            "email": "login@example.com",
            "password": "correct-password",
            "full_name": "Login User",
            "organization_name": "Login Org",
        },
    )
    response = await client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "wrong-password"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


async def test_me_requires_authentication(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


async def test_me_returns_current_user(client: AsyncClient):
    register = await client.post(
        "/api/auth/register",
        json={
            "email": "me@example.com",
            "password": "supersecret1",
            "full_name": "Me User",
            "organization_name": "Me Org",
        },
    )
    token = register.json()["access_token"]

    response = await client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "me@example.com"
    assert body["role"] == "admin"


async def test_health_endpoint(client: AsyncClient):
    response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
