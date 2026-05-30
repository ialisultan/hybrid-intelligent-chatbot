"""FastAPI route definitions."""

from fastapi import APIRouter

from src.adapters.api.routes.chat import router as chat_router
from src.adapters.api.routes.classification import router as classification_router
from src.adapters.api.routes.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(chat_router, prefix="/api/v1", tags=["chat"])
api_router.include_router(classification_router, prefix="/api/v1", tags=["classification"])
