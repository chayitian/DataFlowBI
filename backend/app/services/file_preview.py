from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pandas as pd
from fastapi import HTTPException, UploadFile

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOADS_DIR = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}


def build_preview(file: UploadFile) -> dict:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload CSV or XLSX.",
        )

    saved_path = _save_upload(file)
    try:
        dataframe = _load_dataframe(saved_path, suffix)
    except Exception as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to parse file: {exc}"
        ) from exc

    fields = [str(col) for col in dataframe.columns.tolist()]
    return {
        "filename": Path(file.filename).name,
        "rows": int(dataframe.shape[0]),
        "columns": int(dataframe.shape[1]),
        "fields": fields,
    }


def _save_upload(file: UploadFile) -> Path:
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
