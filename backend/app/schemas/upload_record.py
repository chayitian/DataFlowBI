from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class UploadRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: Optional[str] = None
    version: Optional[int] = None
    parent_id: Optional[int] = None
    tag: Optional[str] = None
    filename: str
    original_filename: str
    file_size: int
    row_count: int
    column_count: int
    columns: list[str]
    imported_table: Optional[str] = None
    import_status: Optional[str] = None
    created_at: datetime


class UploadRecordListResponse(BaseModel):
    records: list[UploadRecordResponse]
    total: int
