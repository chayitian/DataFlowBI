"""上传解析、内存数据集缓存、筛选和清洗。

核心生命周期：
1. 上传文件会带 UUID 前缀复制到 backend/uploads。
2. pandas 解析复制后的文件，并写入 DATA_CACHE 以支持交互操作。
3. PostgreSQL 可用时，元数据会写入 upload_records。
4. 清洗会创建新的快照文件，不会覆盖源文件。
"""

from __future__ import annotations

import hashlib
import logging
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile

from app.config import AUTO_IMPORT_DB, IMPORT_IF_EXISTS
from app.database.db import SessionLocal
from app.models import UploadRecord
from app.services.db_import import build_table_name, import_dataframe
from app.services.report_builder import build_report, build_quality

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

logger = logging.getLogger(__name__)

# 进程内缓存，按 saved_name 索引。它能让图表、清洗和 ML 更快，但不具备持久性；
# 历史重载可以根据磁盘上的 cached_path 重新填充它。
DATA_CACHE: dict[str, pd.DataFrame] = {}


def _display_dtype(dtype: Any) -> str:
    name = str(dtype)
    return "object" if name in ("str", "string") else name


def build_preview(file: UploadFile) -> dict:
    """保存上传文件、解析并缓存，然后返回前端预览数据。"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload CSV or XLSX.",
        )

    saved_path = _save_upload(file, suffix)
    try:
        dataframe = _load_dataframe(saved_path, suffix)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to parse file: {exc}"
        ) from exc

    saved_name = saved_path.name
    DATA_CACHE[saved_name] = dataframe

    fields = [str(col) for col in dataframe.columns.tolist()]
    report = build_report(dataframe)
    filter_info = build_filter_info(dataframe)

    record_id = None
    dataset_id = uuid.uuid4().hex
    version = 1
    file_hash = _compute_file_hash(saved_path)

    imported_table = None
    import_status = None
    imported_at = None
    # 可选 SQL 导入采用尽力而为策略；导入失败不应阻塞预览。
    if AUTO_IMPORT_DB:
        try:
            imported_table = build_table_name(dataset_id, version)
            import_dataframe(dataframe, imported_table, if_exists=IMPORT_IF_EXISTS)
            import_status = "success"
            imported_at = datetime.utcnow()
        except Exception as exc:
            import_status = "failed"
            logger.warning("Auto import failed: %s", exc)

    # 历史持久化同样采用尽力而为策略，保证无数据库时应用仍可工作。
    db = SessionLocal()
    try:
        record = UploadRecord(
            dataset_id=dataset_id,
            version=version,
            parent_id=None,
            tag="original",
            filename=saved_name,
            original_filename=Path(file.filename).name,
            file_size=saved_path.stat().st_size,
            file_hash=file_hash,
            row_count=int(dataframe.shape[0]),
            column_count=int(dataframe.shape[1]),
            columns_json=fields,
            dtypes_json={str(col): str(dtype) for col, dtype in dataframe.dtypes.items()},
            cached_path=str(saved_path),
            cleaning_log_json=None,
            comparison_json=None,
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
        "saved_name": saved_name,
        "filename": Path(file.filename).name,
        "dataset_id": dataset_id,
        "version": version,
        "rows": int(dataframe.shape[0]),
        "columns": int(dataframe.shape[1]),
        "fields": fields,
        "report": report,
        "filter_info": filter_info,
        "record_id": record_id,
    }


def rebin_histogram(saved_name: str, field: str, bin_count: int, normalize: bool) -> dict:
    """为已上传数据中的数值字段重新计算直方图分箱。"""
    dataframe = DATA_CACHE.get(saved_name)
    if dataframe is None:
        raise HTTPException(status_code=404, detail="Session expired or file not found. Please re-upload.")

    if field not in dataframe.columns:
        raise HTTPException(status_code=400, detail=f"Field '{field}' not found.")

    series = dataframe[field].dropna()
    if not pd.api.types.is_numeric_dtype(series):
        raise HTTPException(status_code=400, detail=f"Field '{field}' is not numeric.")

    if series.empty:
        raise HTTPException(status_code=400, detail=f"Field '{field}' has no data.")

    unique_values = max(1, int(series.nunique()))
    actual_bins = min(bin_count, unique_values)
    counts, bin_edges = np.histogram(series.to_numpy(), bins=actual_bins)

    if normalize:
        total = counts.sum()
        if total > 0:
            counts = counts.astype(float) / total

    return {
        "field": field,
        "bin_count": actual_bins,
        "normalize": normalize,
        "bins": [float(v) for v in bin_edges.tolist()],
        "counts": [float(v) if normalize else int(v) for v in counts.tolist()],
    }


def filter_data(
    saved_name: str,
    include_fields: Optional[List[str]] = None,
    numeric_ranges: Optional[Dict[str, List[float]]] = None,
    categorical_values: Optional[Dict[str, List[str]]] = None,
) -> dict:
    """应用仅用于预览的筛选，不创建新的保存快照。"""
    dataframe = DATA_CACHE.get(saved_name)
    if dataframe is None:
        raise HTTPException(status_code=404, detail="Session expired or file not found. Please re-upload.")

    df = dataframe.copy()

    if include_fields:
        valid = [c for c in include_fields if c in df.columns]
        if valid:
            df = df[valid]

    if numeric_ranges:
        for field, (lo, hi) in numeric_ranges.items():
            if field in df.columns and pd.api.types.is_numeric_dtype(df[field]):
                df = df[(df[field] >= lo) & (df[field] <= hi)]

    if categorical_values:
        for field, vals in categorical_values.items():
            if field in df.columns:
                df = df[df[field].astype(str).isin(vals)]

    report = build_report(df)
    fields = [str(col) for col in df.columns.tolist()]
    return {
        "fields": fields,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "report": report,
    }


def build_filter_info(dataframe: pd.DataFrame) -> dict:
    """构建筛选、清洗和 ML 弹窗使用的列级元数据。"""
    info = {}
    for col in dataframe.columns:
        entry = {"dtype": _display_dtype(dataframe[col].dtype)}
        series = dataframe[col].dropna()
        if pd.api.types.is_numeric_dtype(series):
            if not series.empty:
                entry["min"] = _normalize_value(series.min())
                entry["max"] = _normalize_value(series.max())
                entry["mean"] = _normalize_value(series.mean())
        elif entry["dtype"] == "object" or pd.api.types.is_string_dtype(series):
            unique = series.unique().tolist()[:50]
            entry["values"] = [_normalize_value(v) for v in unique]
        entry.update(_suggest_type(dataframe[col]))
        info[str(col)] = entry
    return info


def _normalize_value(value: Any) -> Any:
    """把 pandas/numpy 标量值转换为可 JSON 序列化的值。"""
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            pass
    return value


def _is_integer_like(series: pd.Series) -> bool:
    if series.empty:
        return False
    values = pd.to_numeric(series, errors="coerce").dropna().to_numpy()
    if not len(values):
        return False
    return np.all(np.isclose(values, np.round(values)))


def _suggest_type(series: pd.Series) -> dict:
    """推断字段可能的语义类型，用于清洗建议。"""
    cleaned = series.dropna()
    if cleaned.empty:
        return {"suggested_type": None, "suggestion_confidence": 0.0}

    if pd.api.types.is_numeric_dtype(series):
        if pd.api.types.is_integer_dtype(series) or _is_integer_like(cleaned):
            return {"suggested_type": "int", "suggestion_confidence": 0.9}
        return {"suggested_type": "float", "suggestion_confidence": 0.9}

    if pd.api.types.is_datetime64_any_dtype(series):
        return {"suggested_type": "datetime", "suggestion_confidence": 0.9}

    numeric = pd.to_numeric(cleaned, errors="coerce")
    numeric_rate = float(numeric.notna().mean()) if len(cleaned) else 0.0
    datetime = pd.to_datetime(cleaned, errors="coerce", format="mixed")
    datetime_rate = float(datetime.notna().mean()) if len(cleaned) else 0.0

    best = max(numeric_rate, datetime_rate)
    if best < 0.6:
        return {"suggested_type": "str", "suggestion_confidence": round(1 - best, 3)}

    if datetime_rate >= numeric_rate:
        return {"suggested_type": "datetime", "suggestion_confidence": round(datetime_rate, 3)}

    suggested = "int" if _is_integer_like(numeric.dropna()) else "float"
    return {"suggested_type": suggested, "suggestion_confidence": round(numeric_rate, 3)}


def _build_clean_summary(df: pd.DataFrame) -> dict:
    """生成清洗或特征工程后的前后对比摘要。"""
    n_rows, n_cols = df.shape
    missing_rate_avg = float(df.isna().mean().mean()) if n_rows else 0.0
    quality = build_quality(df)
    return {
        "rows": int(n_rows),
        "columns": int(n_cols),
        "missing_rate_avg": _normalize_value(missing_rate_avg),
        "quality_overall": quality.get("overall", 0.0),
    }


def _compute_file_hash(filepath: Path) -> str:
    """计算缓存文件哈希，让历史记录能标识精确快照。"""
    sha256 = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def _save_upload(file: UploadFile, suffix: str) -> Path:
    """把原始上传文件复制到 backend/uploads，且不修改原文件。"""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload").name
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    destination = UPLOADS_DIR / unique_name

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file.file.close()
    return destination


def _save_dataframe_snapshot(dataframe: pd.DataFrame, original_filename: str) -> Path:
    """把派生数据保存为新文件，而不是替换上传文件。"""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = Path(original_filename).suffix.lower() or ".csv"
    stem = Path(original_filename).stem or "data"
    unique_name = f"{uuid.uuid4().hex}_{stem}{suffix}"
    destination = UPLOADS_DIR / unique_name

    if suffix == ".xlsx":
        dataframe.to_excel(destination, index=False)
    else:
        dataframe.to_csv(destination, index=False)

    return destination


def reload_from_cache(cached_path: str, original_filename: str) -> dict:
    """从磁盘把历史快照重新加载到 DATA_CACHE。"""
    file_path = Path(cached_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Cached file not found on disk.")

    suffix = file_path.suffix.lower()
    try:
        dataframe = _load_dataframe(file_path, suffix)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to parse cached file: {exc}") from exc

    saved_name = file_path.name
    DATA_CACHE[saved_name] = dataframe

    fields = [str(col) for col in dataframe.columns.tolist()]
    report = build_report(dataframe)
    filter_info = build_filter_info(dataframe)
    return {
        "saved_name": saved_name,
        "filename": original_filename,
        "rows": int(dataframe.shape[0]),
        "columns": int(dataframe.shape[1]),
        "fields": fields,
        "report": report,
        "filter_info": filter_info,
    }


def _load_dataframe(file_path: Path, suffix: str) -> pd.DataFrame:
    """把支持的表格文件格式读取为 pandas DataFrame。"""
    if suffix == ".csv":
        return pd.read_csv(file_path)

    return pd.read_excel(file_path)


def clean_data(
    saved_name: str,
    missing_handling: Optional[Dict[str, Dict[str, Any]]] = None,
    outlier_handling: Optional[Dict[str, Dict[str, Any]]] = None,
    type_conversions: Optional[Dict[str, str]] = None,
) -> dict:
    """应用类型转换、缺失值处理和离群值处理。

    清洗从缓存 DataFrame 的副本开始，并写入新的快照文件。
    磁盘上的原始上传文件保持不变。
    """
    dataframe = DATA_CACHE.get(saved_name)
    if dataframe is None:
        raise HTTPException(status_code=404, detail="Session expired or file not found. Please re-upload.")

    df = dataframe.copy()
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
    cleaning_log: list[dict] = []

    # 类型转换先执行，确保后续缺失值/离群值规则看到预期的数值或日期 dtype。
    if type_conversions:
        for field, target_type in type_conversions.items():
            if field not in df.columns:
                continue
            try:
                before = str(df[field].dtype)
                if target_type == "int":
                    df[field] = pd.to_numeric(df[field], errors="coerce").astype("Int64")
                elif target_type == "float":
                    df[field] = pd.to_numeric(df[field], errors="coerce")
                elif target_type == "str":
                    df[field] = df[field].astype(str)
                elif target_type == "datetime":
                    df[field] = pd.to_datetime(df[field], errors="coerce")
                cleaning_log.append({
                    "operation": "type_conversion",
                    "field": field,
                    "detail": f"{before} -> {target_type}",
                })
            except Exception as exc:
                cleaning_log.append({
                    "operation": "type_conversion",
                    "field": field,
                    "detail": f"failed: {exc}",
                })

    # 缺失值规则由 CleanPanel.vue 按字段配置。
    if missing_handling:
        for field, config in missing_handling.items():
            if field not in df.columns:
                continue
            method = config.get("method", "drop")
            try:
                before_count = int(df[field].isna().sum())
                if method == "drop":
                    df = df.dropna(subset=[field])
                elif method == "fill_mean":
                    if pd.api.types.is_numeric_dtype(df[field]):
                        df[field] = df[field].fillna(df[field].mean())
                elif method == "fill_median":
                    if pd.api.types.is_numeric_dtype(df[field]):
                        df[field] = df[field].fillna(df[field].median())
                elif method == "fill_mode":
                    mode_vals = df[field].mode()
                    if not mode_vals.empty:
                        df[field] = df[field].fillna(mode_vals[0])
                elif method == "fill_value":
                    val = config.get("value")
                    if val is not None:
                        df[field] = df[field].fillna(val)
                elif method == "fill_ffill":
                    df[field] = df[field].ffill()
                elif method == "fill_bfill":
                    df[field] = df[field].bfill()
                after_count = int(df[field].isna().sum())
                filled = before_count - after_count
                if filled > 0 or method == "drop":
                    cleaning_log.append({
                        "operation": "missing_handling",
                        "field": field,
                        "method": method,
                        "missing_before": before_count,
                        "missing_after": after_count,
                        "rows_affected": filled if method != "drop" else before_count,
                    })
            except Exception as exc:
                cleaning_log.append({
                    "operation": "missing_handling",
                    "field": field,
                    "detail": f"failed: {exc}",
                })

    # 离群值处理目前支持 IQR 围栏和 z-score 阈值。
    if outlier_handling:
        for field, config in outlier_handling.items():
            if field not in df.columns or not pd.api.types.is_numeric_dtype(df[field]):
                continue
            method = config.get("method", "iqr")
            threshold = float(config.get("threshold", 1.5))
            action = config.get("action", "remove")

            series = df[field].dropna()
            if series.empty:
                continue
            try:
                if method == "iqr":
                    q1 = series.quantile(0.25)
                    q3 = series.quantile(0.75)
                    iqr = q3 - q1
                    lower = q1 - threshold * iqr
                    upper = q3 + threshold * iqr
                    outlier_mask = (df[field] < lower) | (df[field] > upper)
                else:
                    mean = series.mean()
                    std = series.std()
                    if std == 0:
                        continue
                    z_scores = (df[field] - mean) / std
                    outlier_mask = z_scores.abs() > threshold

                outlier_count = int(outlier_mask.sum())
                if outlier_count == 0:
                    continue

                before_rows = df.shape[0]
                if action == "remove":
                    df = df[~outlier_mask]
                else:
                    if method == "iqr":
                        df[field] = df[field].clip(lower, upper)
                    else:
                        capped = df[field].copy()
                        capped[outlier_mask] = df[field].mean()
                        df[field] = capped

                cleaning_log.append({
                    "operation": "outlier_handling",
                    "field": field,
                    "method": method,
                    "action": action,
                    "threshold": threshold,
                    "outlier_count": outlier_count,
                    "rows_affected": before_rows - df.shape[0] if action == "remove" else outlier_count,
                })
            except Exception as exc:
                cleaning_log.append({
                    "operation": "outlier_handling",
                    "field": field,
                    "detail": f"failed: {exc}",
                })

    cleaned_path = _save_dataframe_snapshot(df, original_filename)
    new_saved_name = cleaned_path.name
    DATA_CACHE[new_saved_name] = df
    # 当前会话里让旧 key 也指向清洗后的数据，保证已有 UI 操作继续基于最新版本执行。
    DATA_CACHE[saved_name] = df
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
    file_hash = _compute_file_hash(cleaned_path)
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
            tag="cleaned",
            filename=new_saved_name,
            original_filename=original_filename,
            file_size=cleaned_path.stat().st_size,
            file_hash=file_hash,
            row_count=int(df.shape[0]),
            column_count=int(df.shape[1]),
            columns_json=fields,
            dtypes_json={str(col): str(dtype) for col, dtype in df.dtypes.items()},
            cached_path=str(cleaned_path),
            cleaning_log_json=cleaning_log,
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
        "report": report,
        "filter_info": filter_info,
        "cleaning_log": cleaning_log,
        "comparison": comparison,
        "record_id": record_id,
    }
