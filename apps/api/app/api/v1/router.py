from fastapi import APIRouter

from app.api.v1 import auth, data_sources, health, workspaces

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(workspaces.router)
api_v1_router.include_router(data_sources.router)
