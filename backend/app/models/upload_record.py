"""持久化和历史记录层使用的 SQLAlchemy 模型。"""

from sqlalchemy import Column, DateTime, Integer, JSON, String, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class UploadRecord(Base):
    """每个数据集快照对应一行记录。

    原始上传、清洗后数据集和特征工程后数据集都会作为同一个 dataset_id 的
    不同版本存储在这里。cached_path 指向 backend/uploads 中的文件；
    imported_table 可选地指向 PostgreSQL 中的数据表。
    """

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
