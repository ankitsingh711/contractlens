import time

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db

router = APIRouter(tags=["health"])

_started_at = time.time()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    db_ok = True
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "uptime_seconds": round(time.time() - _started_at, 1),
        "database": "ok" if db_ok else "unavailable",
        "demo_mode": get_settings().is_demo_mode,
    }


@router.get("/metrics")
async def metrics():
    # Populated further in the observability phase (latency, tokens, cost).
    return {
        "requests_total": None,
        "avg_latency_ms": None,
        "note": "Detailed metrics are wired up in the observability phase.",
    }
