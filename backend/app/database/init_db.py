import logging

from sqlalchemy import inspect, text

from app.database.db import engine
from app.models import UploadRecord

logger = logging.getLogger(__name__)

UPLOAD_RECORDS_COLUMNS = {
    "dataset_id": "dataset_id VARCHAR(64) NULL",
    "version": "version INT NULL",
    "parent_id": "parent_id INT NULL",
    "tag": "tag VARCHAR(32) NULL",
    "cleaning_log_json": "cleaning_log_json JSON NULL",
    "comparison_json": "comparison_json JSON NULL",
    "imported_table": "imported_table VARCHAR(255) NULL",
    "import_status": "import_status VARCHAR(32) NULL",
    "imported_at": "imported_at DATETIME NULL",
}


def _upgrade_upload_records_schema() -> None:
    inspector = inspect(engine)
    if "upload_records" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("upload_records")}
    try:
        with engine.begin() as conn:
            for name, ddl in UPLOAD_RECORDS_COLUMNS.items():
                if name not in existing:
                    conn.execute(text(f"ALTER TABLE upload_records ADD COLUMN {ddl}"))

            indexes = {idx["name"] for idx in inspector.get_indexes("upload_records")}
            if "idx_upload_records_dataset_id" not in indexes:
                conn.execute(text("CREATE INDEX idx_upload_records_dataset_id ON upload_records (dataset_id)"))
    except Exception as exc:
        logger.warning("Schema upgrade skipped: %s", exc)


def init_database():
    UploadRecord.metadata.create_all(bind=engine)
    _upgrade_upload_records_schema()


if __name__ == "__main__":
    init_database()
    print("Database tables created successfully.")
