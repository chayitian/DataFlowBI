"""后端所有 API 模块的统一路由注册入口。"""

from fastapi import APIRouter

from app.api import clean, export, feature_engineering, filter, health, history, ml, rebin, upload

api_router = APIRouter()

# 每个模块维护自己的 URL 路径，把 include 集中在这里便于从一个文件查看完整 API 面。
api_router.include_router(health.router, tags=["health"])
api_router.include_router(upload.router, tags=["upload"])
api_router.include_router(clean.router, tags=["clean"])
api_router.include_router(rebin.router, tags=["rebin"])
api_router.include_router(filter.router, tags=["filter"])
api_router.include_router(history.router)
api_router.include_router(export.router)
api_router.include_router(ml.router)
api_router.include_router(feature_engineering.router)
