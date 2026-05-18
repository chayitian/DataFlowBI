import re

import pandas as pd

from app.database.db import engine


def sanitize_table_name(name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", str(name))
    if not safe or safe[0].isdigit():
        safe = f"t_{safe}"
    return safe.lower()


def build_table_name(dataset_id: str, version: int) -> str:
    safe = sanitize_table_name(dataset_id)
    return f"df_{safe}_v{version}"


def import_dataframe(df: pd.DataFrame, table_name: str, if_exists: str = "replace") -> None:
    df.to_sql(table_name, engine, if_exists=if_exists, index=False, chunksize=1000)
