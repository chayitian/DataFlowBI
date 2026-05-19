from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler


@dataclass
class SplitResult:
    x_train: pd.DataFrame
    x_val: Optional[pd.DataFrame]
    x_test: pd.DataFrame
    y_train: pd.Series
    y_val: Optional[pd.Series]
    y_test: pd.Series
    dropped_rows: int


def _coerce_datetime(series: pd.Series) -> pd.Series:
    converted = pd.to_datetime(series, errors="coerce", format="mixed")
    numeric = converted.view("int64")
    numeric = numeric.astype("float64")
    numeric[converted.isna()] = np.nan
    return pd.Series(numeric, index=series.index)


def _prepare_dataframe(
    df: pd.DataFrame,
    target: str,
    features: List[str],
    time_column: Optional[str],
    split_strategy: str,
) -> Tuple[pd.DataFrame, pd.Series, int]:
    if target not in df.columns:
        raise ValueError(f"Target '{target}' not found in data.")

    missing_features = [f for f in features if f not in df.columns]
    if missing_features:
        raise ValueError(f"Feature(s) not found: {', '.join(missing_features)}")

    data = df[features + [target]].copy()
    data = data.dropna(subset=[target])

    dropped = len(df) - len(data)

    for col in features:
        if pd.api.types.is_datetime64_any_dtype(data[col]):
            data[col] = _coerce_datetime(data[col])

    if split_strategy == "time_series" and time_column:
        if time_column not in data.columns:
            data[time_column] = df[time_column]
        if pd.api.types.is_datetime64_any_dtype(data[time_column]):
            time_series = pd.to_datetime(data[time_column], errors="coerce", format="mixed")
        else:
            time_series = pd.to_datetime(data[time_column], errors="coerce", format="mixed")
        valid_mask = time_series.notna()
        dropped += int((~valid_mask).sum())
        data = data.loc[valid_mask].copy()
        time_series = time_series.loc[valid_mask]
        data = data.assign(_time_sort=time_series).sort_values("_time_sort").drop(columns=["_time_sort"])

    y = data[target]
    x = data[features]
    return x, y, dropped


def _split_data(
    x: pd.DataFrame,
    y: pd.Series,
    split_strategy: str,
    test_size: float,
    val_size: Optional[float],
    random_state: int,
    stratify: Optional[pd.Series],
) -> SplitResult:
    if test_size <= 0 or test_size >= 0.9:
        raise ValueError("test_size must be between 0 and 0.9")
    if val_size is not None and (val_size < 0 or val_size >= 0.9):
        raise ValueError("val_size must be between 0 and 0.9")

    if split_strategy == "time_series":
        n = len(x)
        if n < 4:
            raise ValueError("Not enough rows for time series split.")
        n_test = max(1, int(n * test_size))
        n_val = max(1, int(n * val_size)) if val_size else 0
        n_train = n - n_test - n_val
        if n_train <= 0:
            raise ValueError("Not enough rows for training after split.")
        train_end = n_train
        val_end = n_train + n_val
        x_train = x.iloc[:train_end]
        y_train = y.iloc[:train_end]
        x_val = x.iloc[train_end:val_end] if n_val > 0 else None
        y_val = y.iloc[train_end:val_end] if n_val > 0 else None
        x_test = x.iloc[val_end:]
        y_test = y.iloc[val_end:]
        return SplitResult(x_train, x_val, x_test, y_train, y_val, y_test, 0)

    x_train_val, x_test, y_train_val, y_test = train_test_split(
        x,
        y,
        test_size=test_size,
        random_state=random_state,
        stratify=stratify,
    )

    if val_size and val_size > 0:
        val_ratio = val_size / (1 - test_size)
        x_train, x_val, y_train, y_val = train_test_split(
            x_train_val,
            y_train_val,
            test_size=val_ratio,
            random_state=random_state,
            stratify=y_train_val if stratify is not None else None,
        )
    else:
        x_train, y_train = x_train_val, y_train_val
        x_val, y_val = None, None

    return SplitResult(x_train, x_val, x_test, y_train, y_val, y_test, 0)


def _build_preprocessor(x_train: pd.DataFrame) -> ColumnTransformer:
    numeric_features = x_train.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = [c for c in x_train.columns if c not in numeric_features]

    numeric_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    return preprocessor


def _get_feature_names(preprocessor: ColumnTransformer, x_train: pd.DataFrame) -> List[str]:
    try:
        names = preprocessor.get_feature_names_out()
        return [str(name) for name in names]
    except Exception:
        numeric_features = x_train.select_dtypes(include=["number"]).columns.tolist()
        categorical_features = [c for c in x_train.columns if c not in numeric_features]
        feature_names: List[str] = []
        feature_names.extend([str(c) for c in numeric_features])
        feature_names.extend([f"{c}_encoded" for c in categorical_features])
        return feature_names


def _get_model(task_type: str, model_type: str, params: Dict[str, Any]):
    if task_type == "regression":
        alpha = float(params.get("alpha", 1.0))
        l1_ratio = float(params.get("l1_ratio", 0.5))
        if model_type == "linear":
            return LinearRegression()
        if model_type == "lasso":
            return Lasso(alpha=alpha, max_iter=5000)
        if model_type == "ridge":
            return Ridge(alpha=alpha)
        if model_type == "elasticnet":
            return ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=5000)
        raise ValueError("Unsupported regression model.")

    if task_type == "classification":
        c_value = float(params.get("c", 1.0))
        l1_ratio = float(params.get("l1_ratio", 0.5))
        if model_type in ("logistic", "logistic_l2"):
            return LogisticRegression(C=c_value, penalty="l2", max_iter=2000)
        if model_type == "logistic_l1":
            return LogisticRegression(C=c_value, penalty="l1", solver="liblinear", max_iter=2000)
        if model_type == "logistic_elasticnet":
            return LogisticRegression(C=c_value, penalty="elasticnet", solver="saga", l1_ratio=l1_ratio, max_iter=4000)
        raise ValueError("Unsupported classification model.")

    raise ValueError("Unsupported task type.")


def _evaluate_regression(model, x, y) -> Dict[str, Any]:
    preds = model.predict(x)
    return {
        "r2": float(r2_score(y, preds)),
        "mae": float(mean_absolute_error(y, preds)),
        "rmse": float(np.sqrt(mean_squared_error(y, preds))),
    }


def _evaluate_classification(model, x, y) -> Dict[str, Any]:
    preds = model.predict(x)
    metrics = {
        "accuracy": float(accuracy_score(y, preds)),
        "precision": float(precision_score(y, preds, average="macro", zero_division=0)),
        "recall": float(recall_score(y, preds, average="macro", zero_division=0)),
        "f1": float(f1_score(y, preds, average="macro", zero_division=0)),
    }
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(x)
        if proba.shape[1] == 2:
            metrics["roc_auc"] = float(roc_auc_score(y, proba[:, 1]))
    metrics["confusion_matrix"] = confusion_matrix(y, preds).tolist()
    return metrics


def _build_ols_summary(x_train, y_train, feature_names: List[str]) -> Dict[str, Any]:
    if hasattr(x_train, "toarray"):
        x_train = x_train.toarray()
    x_df = pd.DataFrame(x_train, columns=feature_names)
    x_df = sm.add_constant(x_df, has_constant="add")
    y_series = pd.Series(y_train).reset_index(drop=True)
    x_df = x_df.reset_index(drop=True)
    model = sm.OLS(y_series, x_df).fit()
    table = model.summary2().tables[1]
    table = table.reset_index().rename(columns={"index": "feature"})
    records = table.to_dict(orient="records")
    return {
        "summary": {
            "r2": float(model.rsquared),
            "adj_r2": float(model.rsquared_adj),
            "aic": float(model.aic),
            "bic": float(model.bic),
            "nobs": int(model.nobs),
        },
        "table": records,
    }


def train_model(
    df: pd.DataFrame,
    task_type: str,
    target: str,
    features: List[str],
    split_strategy: str,
    test_size: float,
    val_size: Optional[float],
    time_column: Optional[str],
    model_type: str,
    params: Dict[str, Any],
    random_state: int = 42,
) -> Dict[str, Any]:
    if not features:
        raise ValueError("At least one feature is required.")
    x, y, dropped = _prepare_dataframe(df, target, features, time_column, split_strategy)

    if task_type == "regression":
        y_numeric = pd.to_numeric(y, errors="coerce")
        before = len(y_numeric)
        y_numeric = y_numeric.dropna()
        dropped += before - len(y_numeric)
        x = x.loc[y_numeric.index]
        y = y_numeric
    classes = None
    if task_type == "classification":
        encoder = LabelEncoder()
        y = pd.Series(encoder.fit_transform(y.astype(str)), index=y.index)
        classes = [str(c) for c in encoder.classes_]

    if y.nunique() < 2:
        raise ValueError("Target must have at least 2 unique values.")

    stratify = y if task_type == "classification" and split_strategy == "random" else None
    split = _split_data(x, y, split_strategy, test_size, val_size, random_state, stratify)

    preprocessor = _build_preprocessor(split.x_train)
    model = _get_model(task_type, model_type, params)
    pipeline = Pipeline(steps=[("preprocess", preprocessor), ("model", model)])
    pipeline.fit(split.x_train, split.y_train)
    feature_names = _get_feature_names(pipeline.named_steps["preprocess"], split.x_train)

    metrics: Dict[str, Any] = {}
    if task_type == "regression":
        metrics["train"] = _evaluate_regression(pipeline, split.x_train, split.y_train)
        metrics["test"] = _evaluate_regression(pipeline, split.x_test, split.y_test)
        if split.x_val is not None:
            metrics["val"] = _evaluate_regression(pipeline, split.x_val, split.y_val)
    else:
        metrics["train"] = _evaluate_classification(pipeline, split.x_train, split.y_train)
        metrics["test"] = _evaluate_classification(pipeline, split.x_test, split.y_test)
        if split.x_val is not None:
            metrics["val"] = _evaluate_classification(pipeline, split.x_val, split.y_val)

    coeffs: List[Dict[str, Any]] = []
    fitted_model = pipeline.named_steps["model"]
    try:
        if hasattr(fitted_model, "coef_"):
            coef = fitted_model.coef_
            if coef.ndim == 1:
                for name, value in zip(feature_names, coef):
                    coeffs.append({"feature": name, "coef": float(value)})
            else:
                for class_idx, row in enumerate(coef):
                    for name, value in zip(feature_names, row):
                        coeffs.append({"class": int(class_idx), "feature": name, "coef": float(value)})
    except Exception:
        coeffs = []

    ols = None
    if task_type == "regression" and model_type == "linear":
        x_train_trans = pipeline.named_steps["preprocess"].transform(split.x_train)
        ols = _build_ols_summary(x_train_trans, split.y_train, feature_names)

    return {
        "task_type": task_type,
        "model_type": model_type,
        "target": target,
        "features": features,
        "classes": classes,
        "split": {
            "strategy": split_strategy,
            "test_size": test_size,
            "val_size": val_size or 0,
            "dropped_rows": dropped,
            "sizes": {
                "train": int(len(split.x_train)),
                "val": int(len(split.x_val)) if split.x_val is not None else 0,
                "test": int(len(split.x_test)),
            },
        },
        "metrics": metrics,
        "coefficients": coeffs,
        "ols": ols,
    }
