"""基于 upload_records 表的历史记录接口。

当 PostgreSQL 不可用时，历史列表允许降级为空列表，保证 UI 仍能加载。
详情、重载和导入接口必须依赖数据库记录，因此数据库失败时返回 503。
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models import UploadRecord
from app.schemas.upload_record import UploadRecordListResponse, UploadRecordResponse
from app.services.file_preview import _build_clean_summary, _load_dataframe, reload_from_cache
from app.config import IMPORT_IF_EXISTS
from app.services.db_import import build_table_name, import_dataframe

router = APIRouter(tags=["history"])


def _database_unavailable() -> HTTPException:
    """构造带有用户可执行提示的数据库故障响应。"""
    return HTTPException(
        status_code=503,
        detail="Database unavailable. Start PostgreSQL and verify POSTGRES_* or DATABASE_URL settings.",
    )


def get_db():
    """FastAPI 依赖：为每个请求创建一个 SQLAlchemy session。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _to_upload_record_response(record: UploadRecord) -> UploadRecordResponse:
    """把数据库模型转换为历史接口响应模型。"""
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


def _to_upload_record_list(records: list[UploadRecord], total: int) -> UploadRecordListResponse:
    """构造历史列表响应，避免多个接口重复字段映射。"""
    return UploadRecordListResponse(
        total=total,
        records=[_to_upload_record_response(record) for record in records],
    )


@router.get("/history", response_model=UploadRecordListResponse)
def list_history(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    # 非关键接口：PostgreSQL 不可用时返回空列表。
    try:
        total = db.query(UploadRecord).count()
        records = (
            db.query(UploadRecord)
            .order_by(UploadRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    except SQLAlchemyError:
        return UploadRecordListResponse(total=0, records=[])
    return _to_upload_record_list(records, total)


@router.get("/history/{record_id}", response_model=UploadRecordResponse)
def get_history_detail(record_id: int, db: Session = Depends(get_db)):
    try:
        record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    except SQLAlchemyError:
        raise _database_unavailable()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return _to_upload_record_response(record)


@router.post("/history/{record_id}/reload")
def reload_record(record_id: int, db: Session = Depends(get_db)):
    # 重载也会回填 DATA_CACHE，让图表、清洗和 ML 可以继续使用。
    try:
        record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    except SQLAlchemyError:
        raise _database_unavailable()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    data = reload_from_cache(record.cached_path, record.original_filename)
    data["dataset_id"] = record.dataset_id
    data["version"] = record.version
    data["record_id"] = record.id
    return data


@router.get("/history/{record_id}/versions", response_model=UploadRecordListResponse)
def list_versions(record_id: int, db: Session = Depends(get_db)):
    try:
        record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    except SQLAlchemyError:
        raise _database_unavailable()
    if not record or not record.dataset_id:
        raise HTTPException(status_code=404, detail="Record not found")

    try:
        records = (
            db.query(UploadRecord)
            .filter(UploadRecord.dataset_id == record.dataset_id)
            .order_by(UploadRecord.version.desc())
            .all()
        )
    except SQLAlchemyError:
        raise _database_unavailable()
    return _to_upload_record_list(records, len(records))


@router.get("/history/compare")
def compare_versions(
    from_id: int = Query(...),
    to_id: int = Query(...),
    db: Session = Depends(get_db),
):
    # 版本对比使用磁盘上的缓存文件，不使用已导入的 SQL 表。
    try:
        from_record = db.query(UploadRecord).filter(UploadRecord.id == from_id).first()
        to_record = db.query(UploadRecord).filter(UploadRecord.id == to_id).first()
    except SQLAlchemyError:
        raise _database_unavailable()
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
    # 手动导入允许用户把已有缓存快照写入 PostgreSQL。
    try:
        record = db.query(UploadRecord).filter(UploadRecord.id == record_id).first()
    except SQLAlchemyError:
        raise _database_unavailable()
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
