"""特征工程服务。

这里的操作会把派生列追加到缓存 DataFrame 的副本上，并把结果保存为新的数据集版本。
它们不会修改用户上传的原始文件。
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.config import AUTO_IMPORT_DB, IMPORT_IF_EXISTS
from app.database.db import SessionLocal
from app.models import UploadRecord
from app.services.db_import import build_table_name, import_dataframe
from app.services.file_preview import (
    DATA_CACHE,
    _build_clean_summary,
    _compute_file_hash,
    _save_dataframe_snapshot,
    build_filter_info,
)
from app.services.report_builder import build_report

logger = logging.getLogger(__name__)


def _unique_column_name(dataframe: pd.DataFrame, base_name: str) -> str:
    """创建派生特征时避免覆盖已有列。"""
    candidate = base_name
    index = 2
    while candidate in dataframe.columns:
        candidate = f"{base_name}_{index}"
        index += 1
    return candidate


def _apply_numeric_transform(df: pd.DataFrame, field: str, method: str) -> Optional[str]:
    """新增标准化或 min-max 归一化后的数值列。"""
    if field not in df.columns:
        return None

    series = pd.to_numeric(df[field], errors="coerce")
    if series.notna().sum() == 0:
        return None

    if method == "standardize":
        std = series.std()
        transformed = series.copy()
        if std and not np.isclose(std, 0):
            transformed = (series - series.mean()) / std
        else:
            transformed.loc[series.notna()] = 0.0
        suffix = "standardized"
    elif method == "normalize":
        min_value = series.min()
        max_value = series.max()
        transformed = series.copy()
        if not np.isclose(max_value - min_value, 0):
            transformed = (series - min_value) / (max_value - min_value)
        else:
            transformed.loc[series.notna()] = 0.0
        suffix = "normalized"
    else:
        return None

    new_field = _unique_column_name(df, f"{field}_{suffix}")
    df[new_field] = transformed
    return new_field


def _apply_one_hot(df: pd.DataFrame, field: str) -> List[str]:
    """把分类字段展开为 0/1 指示列。"""
    if field not in df.columns:
        return []

    dummies = pd.get_dummies(df[field], prefix=field, dummy_na=False, dtype=int)
    new_fields: List[str] = []
    for column in dummies.columns:
        new_field = _unique_column_name(df, str(column))
        df[new_field] = dummies[column]
        new_fields.append(new_field)
    return new_fields


def _apply_datetime_parts(df: pd.DataFrame, field: str) -> List[str]:
    """从日期类字段中提取年、月、日和星期列。"""
    if field not in df.columns:
        return []

    series = pd.to_datetime(df[field], errors="coerce", format="mixed")
    parts = {
        "year": series.dt.year,
        "month": series.dt.month,
        "day": series.dt.day,
        "weekday": series.dt.weekday,
    }
    new_fields: List[str] = []
    for suffix, values in parts.items():
        new_field = _unique_column_name(df, f"{field}_{suffix}")
        df[new_field] = values
        new_fields.append(new_field)
    return new_fields


def engineer_features(
    saved_name: str,
    numeric_transforms: Optional[Dict[str, str]] = None,
    categorical_fields: Optional[List[str]] = None,
    datetime_fields: Optional[List[str]] = None,
) -> dict:
    """创建特征工程后的数据集快照，并返回预览/报告数据。"""
    dataframe = DATA_CACHE.get(saved_name)
    if dataframe is None:
        raise HTTPException(status_code=404, detail="Session expired or file not found. Please re-upload.")

    df = dataframe.copy()
    original_fields = [str(col) for col in df.columns.tolist()]
    dataset_id = None
    version = 1
    parent_id = None
    original_filename = Path(saved_name).name if saved_name else "dataset"
    db = SessionLocal()
    try:
        record = db.query(UploadRecord).filter(UploadRecord.filename == saved_name).order_by(UploadRecord.id.desc()).first()
        if record:
            dataset_id = record.dataset_id or uuid.uuid4().hex
            version = (record.version or 1) + 1
            parent_id = record.id
            original_filename = record.original_filename
    except Exception:
        pass
    finally:
        db.close()
    if dataset_id is None:
        dataset_id = uuid.uuid4().hex

    before_summary = _build_clean_summary(df)
    engineering_log: List[Dict[str, Any]] = []

    # 每个请求操作独立执行，避免一个无效字段阻止其他有效特征工程步骤成功。
    for field, method in (numeric_transforms or {}).items():
        new_field = _apply_numeric_transform(df, field, method)
        if new_field:
            engineering_log.append({
                "operation": "numeric_transform",
                "field": field,
                "method": method,
                "created_fields": [new_field],
            })

    for field in categorical_fields or []:
        new_fields = _apply_one_hot(df, field)
        if new_fields:
            engineering_log.append({
                "operation": "one_hot_encoding",
                "field": field,
                "created_fields": new_fields,
            })

    for field in datetime_fields or []:
        new_fields = _apply_datetime_parts(df, field)
        if new_fields:
            engineering_log.append({
                "operation": "datetime_parts",
                "field": field,
                "created_fields": new_fields,
            })

    if not engineering_log:
        raise HTTPException(status_code=400, detail="Select at least one valid feature engineering operation.")

    # 持久化为新的快照文件，历史记录和版本链路会指向它。
    engineered_path = _save_dataframe_snapshot(df, original_filename)
    new_saved_name = engineered_path.name
    DATA_CACHE[new_saved_name] = df
    report = build_report(df)
    fields = [str(col) for col in df.columns.tolist()]
    filter_info = build_filter_info(df)
    after_summary = _build_clean_summary(df)
    comparison = {
        "before": before_summary,
        "after": after_summary,
        "delta": {
            "rows": after_summary["rows"] - before_summary["rows"],
            "columns": after_summary["columns"] - before_summary["columns"],
            "missing_rate_avg": (
                (after_summary["missing_rate_avg"] or 0) - (before_summary["missing_rate_avg"] or 0)
            ),
            "quality_overall": after_summary["quality_overall"] - before_summary["quality_overall"],
        },
    }

    record_id = None
    file_hash = _compute_file_hash(engineered_path)
    imported_table = None
    import_status = None
    imported_at = None
    if AUTO_IMPORT_DB:
        try:
            imported_table = build_table_name(dataset_id, version)
            import_dataframe(df, imported_table, if_exists=IMPORT_IF_EXISTS)
            import_status = "success"
            imported_at = datetime.utcnow()
        except Exception as exc:
            import_status = "failed"
            logger.warning("Auto import failed: %s", exc)

    db = SessionLocal()
    try:
        record = UploadRecord(
            dataset_id=dataset_id,
            version=version,
            parent_id=parent_id,
            tag="feature_engineered",
            filename=new_saved_name,
            original_filename=original_filename,
            file_size=engineered_path.stat().st_size,
            file_hash=file_hash,
            row_count=int(df.shape[0]),
            column_count=int(df.shape[1]),
            columns_json=fields,
            dtypes_json={str(col): str(dtype) for col, dtype in df.dtypes.items()},
            cached_path=str(engineered_path),
            cleaning_log_json=engineering_log,
            comparison_json=comparison,
            imported_table=imported_table,
            import_status=import_status,
            imported_at=imported_at,
        )
        db.add(record)
        db.commit()
        record_id = record.id
    except Exception:
        db.rollback()
    finally:
        db.close()

    return {
        "saved_name": new_saved_name,
        "filename": original_filename,
        "dataset_id": dataset_id,
        "version": version,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "fields": fields,
        "original_fields": original_fields,
        "engineered_fields": [
            field
            for log in engineering_log
            for field in log.get("created_fields", [])
        ],
        "report": report,
        "filter_info": filter_info,
        "feature_engineering_log": engineering_log,
        "comparison": comparison,
        "record_id": record_id,
    }
