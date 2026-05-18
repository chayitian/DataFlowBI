from typing import Any, Dict, Optional

from fastapi import APIRouter, Body

from app.services.file_preview import clean_data

router = APIRouter()


CLEAN_TEMPLATES = [
    {
        "id": "safe",
        "label_key": "cleanTemplateSafe",
        "desc_key": "cleanTemplateSafeDesc",
        "missing": {
            "numeric": {"method": "fill_mean"},
            "categorical": {"method": "fill_mode"},
            "datetime": {"method": "fill_ffill"},
        },
        "outlier": {
            "numeric": {"method": "iqr", "threshold": 1.5, "action": "cap"},
        },
        "type_conversion": {"use_suggestions": True, "min_confidence": 0.9},
    },
    {
        "id": "balanced",
        "label_key": "cleanTemplateBalanced",
        "desc_key": "cleanTemplateBalancedDesc",
        "missing": {
            "numeric": {"method": "fill_median"},
            "categorical": {"method": "fill_mode"},
            "datetime": {"method": "fill_ffill"},
        },
        "outlier": {
            "numeric": {"method": "iqr", "threshold": 1.5, "action": "cap"},
        },
        "type_conversion": {"use_suggestions": True, "min_confidence": 0.85},
    },
    {
        "id": "aggressive",
        "label_key": "cleanTemplateAggressive",
        "desc_key": "cleanTemplateAggressiveDesc",
        "missing": {
            "numeric": {"method": "drop"},
            "categorical": {"method": "drop"},
            "datetime": {"method": "drop"},
        },
        "outlier": {
            "numeric": {"method": "iqr", "threshold": 1.5, "action": "remove"},
        },
        "type_conversion": {"use_suggestions": True, "min_confidence": 0.7},
    },
]


@router.get("/clean/templates")
def clean_templates() -> Dict[str, Any]:
    return {"templates": CLEAN_TEMPLATES}


@router.post("/clean")
def clean(
    saved_name: str = Body(...),
    missing_handling: Optional[Dict[str, Dict[str, Any]]] = Body(default=None),
    outlier_handling: Optional[Dict[str, Dict[str, Any]]] = Body(default=None),
    type_conversions: Optional[Dict[str, str]] = Body(default=None),
) -> Dict[str, Any]:
    return clean_data(saved_name, missing_handling, outlier_handling, type_conversions)
