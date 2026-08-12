import os
from collections.abc import AsyncGenerator

# Point the app at an isolated test database *before* any app module is
# imported, so the app's own engine/session factory (used both by request
# handlers and by background tasks like document processing) targets it.
_settings_url = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://contractlens:contractlens@localhost:5433/contractlens",
)
os.environ["DATABASE_URL"] = _settings_url.rsplit("/", 1)[0] + "/contractlens_test"

import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    # The engine's connection pool is bound to this test's event loop, which
    # pytest-asyncio tears down after each test — dispose it so the next
    # test (a new loop) doesn't reuse now-invalid pooled connections.
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
