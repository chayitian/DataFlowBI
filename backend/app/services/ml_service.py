"""基于 pandas、sklearn 和 statsmodels 的模型训练服务。

整体流程是：校验列、准备目标和特征、划分数据、构建预处理 pipeline、训练所选模型，
然后向前端返回指标和模型解释信息。
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import ElasticNet, HuberRegressor, Lasso, LinearRegression, LogisticRegression, Ridge
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
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor


@dataclass
class SplitResult:
    """train_model 使用的训练/验证/测试集划分容器。"""

    x_train: pd.DataFrame
    x_val: Optional[pd.DataFrame]
    x_test: pd.DataFrame
    y_train: pd.Series
    y_val: Optional[pd.Series]
    y_test: pd.Series
    dropped_rows: int


def _coerce_datetime(series: pd.Series) -> pd.Series:
    """把日期时间转换为数值时间戳，便于 sklearn 使用。"""
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
    """校验所选列，并在划分前准备 x/y。"""
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

    # 时间序列划分要求按有效的日期类字段排序行。
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
    """按随机或时间顺序划分数据，可选验证集。"""
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


def _build_onehot_encoder() -> OneHotEncoder:
    """兼容不同 sklearn 版本中 sparse/sparse_output 参数名变化。"""
    try:
        return OneHotEncoder(handle_unknown="ignore", sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", sparse=False)


def _build_preprocessor(x_train: pd.DataFrame) -> ColumnTransformer:
    """创建数值和分类特征的预处理 pipeline。"""
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
            ("onehot", _build_onehot_encoder()),
        ]
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ]
    )

    return preprocessor


def _format_prefixed_feature_name(name: str, categorical_features: List[str]) -> str:
    display_name = name.split("__", 1)[1] if "__" in name else name
    for field in sorted(categorical_features, key=len, reverse=True):
        prefix = f"{field}_"
        if display_name.startswith(prefix):
            return f"{field}={display_name[len(prefix):]}"
    return display_name


def _get_feature_names(preprocessor: ColumnTransformer, x_train: pd.DataFrame) -> List[str]:
    """返回独热编码后用户可读的特征名。"""
    numeric_features = x_train.select_dtypes(include=["number"]).columns.tolist()
    categorical_features = [c for c in x_train.columns if c not in numeric_features]

    try:
        feature_names: List[str] = [str(c) for c in numeric_features]
        categorical_transformer = preprocessor.named_transformers_.get("cat")
        if categorical_features and categorical_transformer not in (None, "drop"):
            onehot = categorical_transformer.named_steps.get("onehot")
            for field, categories in zip(categorical_features, onehot.categories_):
                feature_names.extend([f"{field}={category}" for category in categories])
        return feature_names
    except Exception:
        try:
            names = preprocessor.get_feature_names_out()
            return [_format_prefixed_feature_name(str(name), categorical_features) for name in names]
        except Exception:
            feature_names = [str(c) for c in numeric_features]
            feature_names.extend([f"{c}_encoded" for c in categorical_features])
            return feature_names


def _is_blank(value: Any) -> bool:
    return value is None or value == ""


def _as_bool(params: Dict[str, Any], key: str, default: bool) -> bool:
    value = params.get(key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)


def _as_float(params: Dict[str, Any], key: str, default: float, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    value = default if _is_blank(params.get(key)) else float(params.get(key))
    if min_value is not None and value < min_value:
        raise ValueError(f"{key} must be >= {min_value}")
    if max_value is not None and value > max_value:
        raise ValueError(f"{key} must be <= {max_value}")
    return value


def _as_int(params: Dict[str, Any], key: str, default: int, min_value: Optional[int] = None, allow_negative: bool = False) -> int:
    value = default if _is_blank(params.get(key)) else int(params.get(key))
    if min_value is not None and value < min_value and not (allow_negative and value < 0):
        raise ValueError(f"{key} must be >= {min_value}")
    return value


def _as_optional_int(params: Dict[str, Any], key: str, default: Optional[int] = None, min_value: Optional[int] = None) -> Optional[int]:
    if _is_blank(params.get(key)):
        return default
    value = int(params.get(key))
    if min_value is not None and value < min_value:
        raise ValueError(f"{key} must be >= {min_value}")
    return value


def _as_choice(params: Dict[str, Any], key: str, default: str, choices: tuple[str, ...]) -> str:
    value = str(params.get(key, default))
    if value not in choices:
        raise ValueError(f"{key} must be one of: {', '.join(choices)}")
    return value


def _tree_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "max_depth": _as_optional_int(params, "max_depth", None, 1),
        "min_samples_split": _as_int(params, "min_samples_split", 2, 2),
        "min_samples_leaf": _as_int(params, "min_samples_leaf", 1, 1),
        "random_state": _as_int(params, "random_state", 42),
    }


def _forest_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        **_tree_params(params),
        "n_estimators": _as_int(params, "n_estimators", 100, 1),
    }


def _boosting_params(params: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "n_estimators": _as_int(params, "n_estimators", 100, 1),
        "learning_rate": _as_float(params, "learning_rate", 0.1, 0.0),
        "max_depth": _as_int(params, "max_depth", 3, 1),
        "random_state": _as_int(params, "random_state", 42),
    }


def _uses_new_logistic_regularization() -> bool:
    """检测 sklearn 是否已改用 l1_ratio 表达 LogisticRegression 正则类型。"""
    try:
        penalty = inspect.signature(LogisticRegression).parameters.get("penalty")
    except (TypeError, ValueError):
        return False
    return penalty is not None and penalty.default == "deprecated"


def _logistic_regression(model_type: str, c_value: float, l1_ratio: float, max_iter: int) -> LogisticRegression:
    """按 sklearn 版本创建逻辑回归，避免新版 penalty 弃用警告。"""
    if _uses_new_logistic_regularization():
        if model_type in ("logistic", "logistic_l2"):
            return LogisticRegression(C=c_value, l1_ratio=0, max_iter=max_iter)
        if model_type == "logistic_l1":
            return LogisticRegression(C=c_value, l1_ratio=1, solver="liblinear", max_iter=max_iter)
        return LogisticRegression(C=c_value, l1_ratio=l1_ratio, solver="saga", max_iter=max_iter)

    if model_type in ("logistic", "logistic_l2"):
        return LogisticRegression(C=c_value, penalty="l2", max_iter=max_iter)
    if model_type == "logistic_l1":
        return LogisticRegression(C=c_value, penalty="l1", solver="liblinear", max_iter=max_iter)
    return LogisticRegression(C=c_value, penalty="elasticnet", solver="saga", l1_ratio=l1_ratio, max_iter=max_iter)


def _get_model(task_type: str, model_type: str, params: Dict[str, Any]):
    """实例化 MachineLearningDialog.vue 中选择的 sklearn 模型。"""
    if task_type == "regression":
        alpha = _as_float(params, "alpha", 1.0, 0.0)
        l1_ratio = _as_float(params, "l1_ratio", 0.5, 0.0, 1.0)
        if model_type == "linear":
            return LinearRegression(fit_intercept=_as_bool(params, "fit_intercept", True))
        if model_type == "lasso":
            return Lasso(alpha=alpha, max_iter=_as_int(params, "max_iter", 5000, 100))
        if model_type == "ridge":
            return Ridge(alpha=alpha)
        if model_type == "elasticnet":
            return ElasticNet(alpha=alpha, l1_ratio=l1_ratio, max_iter=_as_int(params, "max_iter", 5000, 100))
        if model_type == "random_forest_regressor":
            return RandomForestRegressor(**_forest_params(params))
        if model_type == "gradient_boosting_regressor":
            return GradientBoostingRegressor(**_boosting_params(params))
        if model_type == "svr":
            return SVR(
                C=_as_float(params, "c", 1.0, 0.001),
                kernel=_as_choice(params, "kernel", "rbf", ("linear", "rbf", "poly", "sigmoid")),
                gamma=_as_choice(params, "gamma", "scale", ("scale", "auto")),
                epsilon=_as_float(params, "epsilon", 0.1, 0.0),
            )
        if model_type == "knn_regressor":
            return KNeighborsRegressor(
                n_neighbors=_as_int(params, "n_neighbors", 5, 1),
                weights=_as_choice(params, "weights", "uniform", ("uniform", "distance")),
                metric=_as_choice(params, "metric", "minkowski", ("minkowski", "euclidean", "manhattan")),
            )
        if model_type == "decision_tree_regressor":
            return DecisionTreeRegressor(
                **_tree_params(params),
                criterion=_as_choice(params, "criterion", "squared_error", ("squared_error", "friedman_mse", "absolute_error")),
            )
        if model_type == "huber":
            return HuberRegressor(
                alpha=_as_float(params, "alpha", 0.0001, 0.0),
                epsilon=_as_float(params, "epsilon", 1.35, 1.0),
                max_iter=_as_int(params, "max_iter", 100, 10),
            )
        raise ValueError("Unsupported regression model.")

    if task_type == "classification":
        c_value = _as_float(params, "c", 1.0, 0.001)
        l1_ratio = _as_float(params, "l1_ratio", 0.5, 0.0, 1.0)
        if model_type in ("logistic", "logistic_l2", "logistic_l1", "logistic_elasticnet"):
            default_max_iter = 4000 if model_type == "logistic_elasticnet" else 2000
            return _logistic_regression(
                model_type,
                c_value,
                l1_ratio,
                _as_int(params, "max_iter", default_max_iter, 100),
            )
        if model_type == "random_forest_classifier":
            return RandomForestClassifier(**_forest_params(params))
        if model_type == "gradient_boosting_classifier":
            return GradientBoostingClassifier(**_boosting_params(params))
        if model_type == "svc":
            return SVC(
                C=c_value,
                kernel=_as_choice(params, "kernel", "rbf", ("linear", "rbf", "poly", "sigmoid")),
                gamma=_as_choice(params, "gamma", "scale", ("scale", "auto")),
                max_iter=_as_int(params, "max_iter", -1, 1, allow_negative=True),
                probability=True,
            )
        if model_type == "knn_classifier":
            return KNeighborsClassifier(
                n_neighbors=_as_int(params, "n_neighbors", 5, 1),
                weights=_as_choice(params, "weights", "uniform", ("uniform", "distance")),
                metric=_as_choice(params, "metric", "minkowski", ("minkowski", "euclidean", "manhattan")),
            )
        if model_type == "decision_tree_classifier":
            return DecisionTreeClassifier(
                **_tree_params(params),
                criterion=_as_choice(params, "criterion", "gini", ("gini", "entropy", "log_loss")),
            )
        if model_type == "gaussian_nb":
            return GaussianNB(var_smoothing=_as_float(params, "var_smoothing", 1e-9, 0.0))
        raise ValueError("Unsupported classification model.")

    raise ValueError("Unsupported task type.")


def _evaluate_regression(model, x, y) -> Dict[str, Any]:
    """计算单个数据划分的回归指标。"""
    preds = model.predict(x)
    return {
        "r2": float(r2_score(y, preds)),
        "mae": float(mean_absolute_error(y, preds)),
        "rmse": float(np.sqrt(mean_squared_error(y, preds))),
    }


def _evaluate_classification(model, x, y) -> Dict[str, Any]:
    """计算单个数据划分的分类指标。"""
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
    """仅普通线性回归使用的 statsmodels OLS 表。"""
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
    """训练一个模型，并返回指标、系数和特征重要性。"""
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
    # sklearn 分类器需要整数编码标签；classes 保留前端展示用的原始标签。
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

    # 线性类模型提供 coef_；树类模型提供特征重要性。
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

    feature_importances: List[Dict[str, Any]] = []
    try:
        if hasattr(fitted_model, "feature_importances_"):
            for name, value in zip(feature_names, fitted_model.feature_importances_):
                feature_importances.append({"feature": name, "importance": float(value)})
            feature_importances.sort(key=lambda item: abs(item["importance"]), reverse=True)
    except Exception:
        feature_importances = []

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
        "feature_importances": feature_importances,
        "ols": ols,
    }
