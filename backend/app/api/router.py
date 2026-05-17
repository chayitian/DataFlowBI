from fastapi import APIRouter

from app.api import export, filter, health, history, rebin, upload

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(rebin.router, tags=["rebin"])
api_router.include_router(filter.router, tags=["filter"])
api_router.include_router(history.router)
api_router.include_router(export.router)
