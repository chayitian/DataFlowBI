from app.database.db import engine
from app.models import UploadRecord


def init_database():
    UploadRecord.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_database()
    print("Database tables created successfully.")
