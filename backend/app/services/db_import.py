"""把 pandas DataFrame 导入 PostgreSQL 表的辅助函数。"""

import re

import pandas as pd

from app.database.db import engine


def sanitize_table_name(name: str) -> str:
    """把用户/数据 ID 转换成安全的 SQL 表名片段。"""
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
    if not safe or safe[0].isdigit():
        safe = f"t_{safe}"
    return safe.lower()


def build_table_name(dataset_id: str, version: int) -> str:
    """让导入表名可追溯到数据集版本历史。"""
    safe = sanitize_table_name(dataset_id)
    return f"df_{safe}_v{version}"


def import_dataframe(df: pd.DataFrame, table_name: str, if_exists: str = "replace") -> None:
    """通过 SQLAlchemy/pandas 把 DataFrame 写入 PostgreSQL。"""
    df.to_sql(table_name, engine, if_exists=if_exists, index=False, chunksize=1000)
