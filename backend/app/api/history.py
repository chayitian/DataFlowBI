from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models import UploadRecord
from app.schemas.upload_record import UploadRecordListResponse, UploadRecordResponse
from app.services.file_preview import reload_from_cache

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
                filename=r.filename,
                original_filename=r.original_filename,
                file_size=r.file_size,
                row_count=r.row_count,
                column_count=r.column_count,
                columns=r.columns_json,
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
        filename=record.filename,
        original_filename=record.original_filename,
        file_size=record.file_size,
        row_count=record.row_count,
        column_count=record.column_count,
        columns=record.columns_json,
        created_at=record.created_at,
    )


@router.post("/history/{record_id}/reload")
def reload_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return reload_from_cache(record.cached_path, record.original_filename)
