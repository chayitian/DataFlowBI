from fastapi import APIRouter, File, HTTPException, Request, UploadFile

from app.config import MAX_FILE_SIZE
from app.services.file_preview import build_preview

router = APIRouter()


@router.post("/upload")
def upload_file(file: UploadFile = File(...), request: Request = None):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {max_mb}MB.",
        )
    return build_preview(file)
