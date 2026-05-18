from sqlalchemy import Column, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UploadRecord(Base):
    __tablename__ = "upload_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dataset_id = Column(String(64), nullable=True, index=True)
    version = Column(Integer, nullable=True, default=1)
    parent_id = Column(Integer, nullable=True)
    tag = Column(String(32), nullable=True, default="original")
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_hash = Column(String(64), nullable=False)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    columns_json = Column(JSON, nullable=False)
    dtypes_json = Column(JSON, nullable=False)
    cached_path = Column(String(500), nullable=False)
    cleaning_log_json = Column(JSON, nullable=True)
    comparison_json = Column(JSON, nullable=True)
    imported_table = Column(String(255), nullable=True)
    import_status = Column(String(32), nullable=True)
    imported_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
