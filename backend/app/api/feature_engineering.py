"""特征工程接口：创建派生数据集快照。"""

from typing import Dict, List

from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

from app.services.feature_engineering import engineer_features

router = APIRouter(tags=["feature_engineering"])


class FeatureEngineeringRequest(BaseModel):
    """FeatureEngineeringDialog.vue 中选择的操作。"""

    saved_name: str
    numeric_transforms: Dict[str, str] = Field(default_factory=dict)
    categorical_fields: List[str] = Field(default_factory=list)
    datetime_fields: List[str] = Field(default_factory=list)


@router.post("/feature-engineering")
def feature_engineering(payload: FeatureEngineeringRequest = Body(...)):
    return engineer_features(
        saved_name=payload.saved_name,
        numeric_transforms=payload.numeric_transforms,
        categorical_fields=payload.categorical_fields,
        datetime_fields=payload.datetime_fields,
    )
