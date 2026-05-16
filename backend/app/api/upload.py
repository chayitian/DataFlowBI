from fastapi import APIRouter, File, UploadFile

from app.services.file_preview import build_preview

router = APIRouter()


@router.post("/upload")
def upload_file(file: UploadFile = File(...)):
    return build_preview(file)
