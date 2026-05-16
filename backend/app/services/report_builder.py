from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


REPORT_SAMPLE_SIZE = 5
HISTOGRAM_BIN_COUNT = 8
HISTOGRAM_FIELD_LIMIT = 8


def build_report(dataframe: pd.DataFrame) -> dict:
    dtypes = {col: str(dtype) for col, dtype in dataframe.dtypes.items()}

    missing = dataframe.isna().sum()
    missing_rate = (missing / len(dataframe)) if len(dataframe) > 0 else missing

    numeric_summary = _build_numeric_summary(dataframe)
    histograms = _build_histograms(dataframe)
    sample_rows = _build_sample_rows(dataframe)

    return {
        "dtypes": dtypes,
        "missing": {col: int(value) for col, value in missing.items()},
        "missing_rate": {col: _normalize_value(value) for col, value in missing_rate.items()},
        "numeric_summary": numeric_summary,
        "histograms": histograms,
        "sample_rows": sample_rows,
    }


def _build_numeric_summary(dataframe: pd.DataFrame) -> dict:
    numeric_df = dataframe.select_dtypes(include="number")
    if numeric_df.empty:
        return {}

    describe = numeric_df.describe().transpose()
    summary = {}

    for column, stats in describe.iterrows():
        summary[column] = {
            "count": _normalize_value(stats.get("count")),
            "mean": _normalize_value(stats.get("mean")),
            "std": _normalize_value(stats.get("std")),
            "min": _normalize_value(stats.get("min")),
            "max": _normalize_value(stats.get("max")),
        }

    return summary


def _build_sample_rows(dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    sample = dataframe.head(REPORT_SAMPLE_SIZE)
    sample = sample.where(pd.notnull(sample), None)
    records = sample.to_dict(orient="records")

    for row in records:
        for key, value in row.items():
            row[key] = _normalize_value(value)

    return records


def _build_histograms(dataframe: pd.DataFrame) -> dict:
    numeric_df = dataframe.select_dtypes(include="number")
    if numeric_df.empty:
        return {}

    histograms: dict[str, dict[str, list]] = {}
    for column in numeric_df.columns[:HISTOGRAM_FIELD_LIMIT]:
        series = numeric_df[column].dropna()
        if series.empty:
            continue

        unique_values = max(1, int(series.nunique()))
        bin_count = min(HISTOGRAM_BIN_COUNT, unique_values)
        counts, bin_edges = np.histogram(series.to_numpy(), bins=bin_count)

        histograms[column] = {
            "bins": [float(value) for value in bin_edges.tolist()],
            "counts": [int(value) for value in counts.tolist()],
        }

    return histograms


def _normalize_value(value: Any) -> Any:
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    if hasattr(value, "item"):
        try:
            return value.item()
        except ValueError:
            pass

    return value
