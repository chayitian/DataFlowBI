from fastapi import APIRouter

from app.api import clean, export, filter, health, history, ml, rebin, upload

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(clean.router, tags=["clean"])
api_router.include_router(rebin.router, tags=["rebin"])
api_router.include_router(filter.router, tags=["filter"])
api_router.include_router(history.router)
api_router.include_router(export.router)
api_router.include_router(ml.router)
