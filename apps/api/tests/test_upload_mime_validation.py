import pytest
from httpx import AsyncClient

from app.services.storage import get_storage_backend

pytestmark = pytest.mark.asyncio


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


async def test_rejects_content_that_does_not_match_declared_pdf_type(client: AsyncClient):
    headers = await _register(client, "mime-fake-pdf@example.com")

    response = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("report.pdf", b"this is not a real pdf file", "application/pdf")},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_rejects_content_that_does_not_match_declared_docx_type(client: AsyncClient):
    headers = await _register(client, "mime-fake-docx@example.com")

    response = await client.post(
        "/api/documents",
        headers=headers,
        files={
            "file": (
                "contract.docx",
                b"not a real docx zip container",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 422


async def test_rejects_binary_content_mislabeled_as_text(client: AsyncClient):
    headers = await _register(client, "mime-fake-txt@example.com")

    # A PDF's actual magic bytes, but mislabeled with a text/plain
    # Content-Type -- the kind of spoofing a malicious client might try.
    response = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("notes.txt", b"%PDF-1.4 fake pdf disguised as text", "text/plain")},
    )
    assert response.status_code == 422


async def test_accepts_genuine_pdf_content(client: AsyncClient):
    headers = await _register(client, "mime-real-pdf@example.com")

    pdf_bytes = (
        b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        b"trailer\n<< /Root 1 0 R >>\n%%EOF"
    )
    response = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("real.pdf", pdf_bytes, "application/pdf")},
    )
    # Parsing may still fail later (no real page content) but the MIME
    # signature check itself must accept a genuine PDF header.
    assert response.status_code == 200


async def test_accepts_genuine_text_content(client: AsyncClient):
    headers = await _register(client, "mime-real-txt@example.com")

    response = await client.post(
        "/api/documents",
        headers=headers,
        files={"file": ("real.txt", b"This is a perfectly normal text document.", "text/plain")},
    )
    assert response.status_code == 200
