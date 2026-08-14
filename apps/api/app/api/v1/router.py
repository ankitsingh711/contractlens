from fastapi import APIRouter

from app.api.v1.agent_runs import router as agent_runs_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router
from app.api.v1.comparisons import router as comparisons_router
from app.api.v1.conversations import router as conversations_router
from app.api.v1.documents import router as documents_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.health import router as health_router
from app.api.v1.search import router as search_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(search_router)
api_router.include_router(chat_router)
api_router.include_router(conversations_router)
api_router.include_router(agent_runs_router)
api_router.include_router(comparisons_router)
api_router.include_router(evaluations_router)
