"""FastAPI 应用工厂和进程级错误处理。

这个文件是 uvicorn 使用的后端入口。路由、数据库启动、CORS 和统一错误响应
都集中在这里，让功能模块只关注各自的业务逻辑。
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.database.init_db import init_database

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _error_response(status_code: int, detail: str, error_type: str) -> JSONResponse:
    """返回前端可稳定处理的统一 JSON 错误结构。"""
    return JSONResponse(
        status_code=status_code,
        content={"error": True, "detail": detail, "type": error_type},
    )


def register_error_handlers(app: FastAPI) -> None:
    """把框架异常和未预期异常转换为稳定的 API 错误。"""
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return _error_response(exc.status_code, exc.detail, "http_error")

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return _error_response(422, str(exc), "validation_error")

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return _error_response(500, "Internal server error. Please try again later.", "server_error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 持久化很有用，但上传/预览流程不强依赖数据库，因此数据库启动失败时
    # 不应阻止应用启动。
    try:
        init_database()
    except Exception:
        logger.warning("Database unavailable, running without persistence")
    yield


def create_app() -> FastAPI:
    """构建 FastAPI 应用；测试会导入它而不是依赖全局对象。"""
    app = FastAPI(title="DATAFLOWBI API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(api_router)
    return app


app = create_app()
