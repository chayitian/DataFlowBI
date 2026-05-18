import os

MAX_FILE_SIZE = 100 * 1024 * 1024
AUTO_IMPORT_DB = os.getenv("AUTO_IMPORT_DB", "0") == "1"
IMPORT_IF_EXISTS = os.getenv("IMPORT_IF_EXISTS", "replace")
