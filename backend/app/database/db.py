"""数据库配置和 SQLAlchemy session 工厂。

部署时 DATABASE_URL 优先级最高。本地开发可以改用 backend/.env 中的 POSTGRES_*
变量；默认值与项目 README 保持一致，便于新装 PostgreSQL 后快速启动。
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "123456")
POSTGRES_DB = os.getenv("POSTGRES_DB", "dataflowbi")


def build_database_url():
    """根据环境变量创建 SQLAlchemy PostgreSQL URL。"""
    configured_url = os.getenv("DATABASE_URL")
    if configured_url:
        return configured_url

    return URL.create(
        "postgresql+psycopg",
        username=os.getenv("POSTGRES_USER", POSTGRES_USER),
        password=os.getenv("POSTGRES_PASSWORD", POSTGRES_PASSWORD),
        host=os.getenv("POSTGRES_HOST", POSTGRES_HOST),
        port=int(os.getenv("POSTGRES_PORT", POSTGRES_PORT)),
        database=os.getenv("POSTGRES_DB", POSTGRES_DB),
    )


DATABASE_URL = build_database_url()

# API 请求和 pandas.to_sql 导入复用同一个 engine。
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args={"connect_timeout": 3})
# FastAPI 依赖会调用 SessionLocal() 创建请求级 session。
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
