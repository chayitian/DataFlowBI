from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: str | None = None
    version: int | None = None
    parent_id: int | None = None
    tag: str | None = None
    filename: str
    original_filename: str
    file_size: int
    row_count: int
    column_count: int
    columns: list[str]
    imported_table: str | None = None
    import_status: str | None = None
    created_at: datetime


class UploadRecordListResponse(BaseModel):
    records: list[UploadRecordResponse]
    total: int
