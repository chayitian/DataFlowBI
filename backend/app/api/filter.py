from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body

from app.services.file_preview import filter_data

router = APIRouter()


@router.post("/filter")
def filter_route(
    saved_name: str = Body(...),
    include_fields: Optional[List[str]] = Body(default=None),
    numeric_ranges: Optional[Dict[str, List[float]]] = Body(default=None),
    categorical_values: Optional[Dict[str, List[str]]] = Body(default=None),
) -> Dict[str, Any]:
    return filter_data(saved_name, include_fields, numeric_ranges, categorical_values)
