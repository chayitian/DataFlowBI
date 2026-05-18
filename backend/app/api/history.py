from datetime import datetime
from pathlib import Path

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models import UploadRecord
from app.schemas.upload_record import UploadRecordListResponse, UploadRecordResponse
from app.services.file_preview import _build_clean_summary, _load_dataframe, reload_from_cache
from app.config import IMPORT_IF_EXISTS
from app.services.db_import import build_table_name, import_dataframe

router = APIRouter(tags=["history"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/history", response_model=UploadRecordListResponse)
def list_history(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    total = db.query(UploadRecord).count()
    records = (
        db.query(UploadRecord)
        .order_by(UploadRecord.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return UploadRecordListResponse(
        total=total,
        records=[
            UploadRecordResponse(
                id=r.id,
                dataset_id=r.dataset_id,
                version=r.version,
                parent_id=r.parent_id,
                tag=r.tag,
                filename=r.filename,
                original_filename=r.original_filename,
                file_size=r.file_size,
                row_count=r.row_count,
                column_count=r.column_count,
                columns=r.columns_json,
                imported_table=r.imported_table,
                import_status=r.import_status,
                created_at=r.created_at,
            )
            for r in records
        ],
    )


@router.get("/history/{record_id}", response_model=UploadRecordResponse)
def get_history_detail(record_id: int, db: Session = Depends(get_db)):
    record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return UploadRecordResponse(
        id=record.id,
        dataset_id=record.dataset_id,
        version=record.version,
        parent_id=record.parent_id,
        tag=record.tag,
        filename=record.filename,
        original_filename=record.original_filename,
        file_size=record.file_size,
        row_count=record.row_count,
        column_count=record.column_count,
        columns=record.columns_json,
        imported_table=record.imported_table,
        import_status=record.import_status,
        created_at=record.created_at,
    )


@router.post("/history/{record_id}/reload")
def reload_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    data = reload_from_cache(record.cached_path, record.original_filename)
    data["dataset_id"] = record.dataset_id
    data["version"] = record.version
    data["record_id"] = record.id
    return data


@router.get("/history/{record_id}/versions", response_model=UploadRecordListResponse)
def list_versions(record_id: int, db: Session = Depends(get_db)):
    record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    if not record or not record.dataset_id:
        raise HTTPException(status_code=404, detail="Record not found")

    records = (
        db.query(UploadRecord)
        .filter(UploadRecord.dataset_id == record.dataset_id)
        .order_by(UploadRecord.version.desc())
        .all()
    )
    return UploadRecordListResponse(
        total=len(records),
        records=[
            UploadRecordResponse(
                id=r.id,
                dataset_id=r.dataset_id,
                version=r.version,
                parent_id=r.parent_id,
                tag=r.tag,
                filename=r.filename,
                original_filename=r.original_filename,
                file_size=r.file_size,
                row_count=r.row_count,
                column_count=r.column_count,
                columns=r.columns_json,
                imported_table=r.imported_table,
                import_status=r.import_status,
                created_at=r.created_at,
            )
            for r in records
        ],
    )


@router.get("/history/compare")
def compare_versions(
    from_id: int = Query(...),
    to_id: int = Query(...),
    db: Session = Depends(get_db),
):
    from_record = db.query(UploadRecord).filter(UploadRecord.id == from_id).first()
    to_record = db.query(UploadRecord).filter(UploadRecord.id == to_id).first()
    if not from_record or not to_record:
        raise HTTPException(status_code=404, detail="Record not found")

    from_df = _load_dataframe(Path(from_record.cached_path), Path(from_record.cached_path).suffix.lower())
    to_df = _load_dataframe(Path(to_record.cached_path), Path(to_record.cached_path).suffix.lower())
    from_summary = _build_clean_summary(from_df)
    to_summary = _build_clean_summary(to_df)

    return {
        "from": {"id": from_record.id, **from_summary},
        "to": {"id": to_record.id, **to_summary},
        "delta": {
            "rows": to_summary["rows"] - from_summary["rows"],
            "columns": to_summary["columns"] - from_summary["columns"],
            "missing_rate_avg": (to_summary["missing_rate_avg"] or 0) - (from_summary["missing_rate_avg"] or 0),
            "quality_overall": to_summary["quality_overall"] - from_summary["quality_overall"],
        },
    }


@router.post("/history/{record_id}/import")
def import_history_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    try:
        dataframe = _load_dataframe(Path(record.cached_path), Path(record.cached_path).suffix.lower())
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    table_name = build_table_name(record.dataset_id or record.id, record.version or 1)
    try:
        import_dataframe(dataframe, table_name, if_exists=IMPORT_IF_EXISTS)
        record.imported_table = table_name
        record.import_status = "success"
        record.imported_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        record.import_status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail=str(exc))

    return {"imported_table": table_name, "status": record.import_status}
