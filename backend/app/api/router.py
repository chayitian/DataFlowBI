from fastapi import APIRouter

from app.api import filter, health, rebin, upload

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(rebin.router, tags=["rebin"])
api_router.include_router(filter.router, tags=["filter"])
