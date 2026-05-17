from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.services.export_service import export_report_docx, export_report_excel

router = APIRouter(prefix="/export", tags=["export"])


def _disposition(filename: str, ext: str) -> str:
    safe = quote(f"{filename}{ext}")
    return f"attachment; filename*=UTF-8''{safe}"


@router.get("/docx")
def export_docx(
    saved_name: str = Query(...),
    filename: str = Query(default="report"),
):
    try:
        docx = export_report_docx(saved_name, filename)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return StreamingResponse(
        docx,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": _disposition(filename, ".docx")},
    )


@router.get("/excel")
def export_excel(
    saved_name: str = Query(...),
    filename: str = Query(default="report"),
):
    try:
        xlsx = export_report_excel(saved_name, filename)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return StreamingResponse(
        xlsx,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": _disposition(filename, ".xlsx")},
    )
