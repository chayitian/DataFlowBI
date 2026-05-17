from datetime import datetime

from pydantic import BaseModel, ConfigDict


class UploadRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    original_filename: str
    file_size: int
    row_count: int
    column_count: int
    columns: list[str]
    created_at: datetime


class UploadRecordListResponse(BaseModel):
    records: list[UploadRecordResponse]
    total: int
