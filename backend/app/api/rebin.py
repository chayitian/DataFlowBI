from fastapi import APIRouter, Query

from app.services.file_preview import rebin_histogram

router = APIRouter()


@router.post("/rebin")
def rebin(
    saved_name: str = Query(...),
    field: str = Query(...),
    bin_count: int = Query(default=10, ge=2, le=100),
    normalize: bool = Query(default=False),
):
    return rebin_histogram(saved_name, field, bin_count, normalize)
