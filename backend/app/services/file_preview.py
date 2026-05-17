from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from fastapi import HTTPException, UploadFile

from app.services.report_builder import build_report

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

DATA_CACHE: dict[str, pd.DataFrame] = {}


def build_preview(file: UploadFile) -> dict:
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
    return {
        "saved_name": saved_name,
        "filename": Path(file.filename).name,
        "rows": int(dataframe.shape[0]),
        "columns": int(dataframe.shape[1]),
        "fields": fields,
        "report": report,
        "filter_info": filter_info,
    }


def rebin_histogram(saved_name: str, field: str, bin_count: int, normalize: bool) -> dict:
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
    info = {}
    for col in dataframe.columns:
        entry = {"dtype": str(dataframe[col].dtype)}
        series = dataframe[col].dropna()
        if pd.api.types.is_numeric_dtype(series):
            if not series.empty:
                entry["min"] = _normalize_value(series.min())
                entry["max"] = _normalize_value(series.max())
                entry["mean"] = _normalize_value(series.mean())
        elif series.dtype == "object":
            unique = series.unique().tolist()[:50]
            entry["values"] = [_normalize_value(v) for v in unique]
        info[str(col)] = entry
    return info


def _normalize_value(value: Any) -> Any:
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


def _save_upload(file: UploadFile, suffix: str) -> Path:
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "upload").name
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    destination = UPLOADS_DIR / unique_name

    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file.file.close()
    return destination


def _load_dataframe(file_path: Path, suffix: str) -> pd.DataFrame:
    if suffix == ".csv":
        return pd.read_csv(file_path)

    return pd.read_excel(file_path)
