"""机器学习 API 接口。"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

from app.services.file_preview import DATA_CACHE
from app.services.ml_service import train_model

router = APIRouter(prefix="/ml", tags=["ml"])


class MLTrainRequest(BaseModel):
    """前端提交的训练请求：在一个缓存数据集上训练一个 sklearn 模型。"""

    saved_name: str = Field(..., description="Cached dataset key")
    task_type: str = Field(..., description="regression | classification")
    target: str
    features: List[str]
    split_strategy: str = Field("random", description="random | time_series")
    time_column: Optional[str] = None
    test_size: float = 0.2
    val_size: Optional[float] = None
    model_type: str = Field("linear", description="model key")
    params: Dict[str, Any] = Field(default_factory=dict)
    random_state: int = 42


@router.post("/train")
def train(payload: MLTrainRequest = Body(...)):
    # 后端把已解析文件保存在 DATA_CACHE 中，saved_name 是缓存键。
    dataframe = DATA_CACHE.get(payload.saved_name)
    if dataframe is None:
        raise HTTPException(status_code=404, detail="Session expired or file not found. Please re-upload.")

    if payload.task_type not in ("regression", "classification"):
        raise HTTPException(status_code=400, detail="Invalid task_type")
    if payload.split_strategy not in ("random", "time_series"):
        raise HTTPException(status_code=400, detail="Invalid split_strategy")
    if payload.split_strategy == "time_series" and not payload.time_column:
        raise HTTPException(status_code=400, detail="time_column is required for time_series split")

    try:
        result = train_model(
            df=dataframe,
            task_type=payload.task_type,
            target=payload.target,
            features=payload.features,
            split_strategy=payload.split_strategy,
            test_size=payload.test_size,
            val_size=payload.val_size,
            time_column=payload.time_column,
            model_type=payload.model_type,
            params=payload.params,
            random_state=payload.random_state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return result
