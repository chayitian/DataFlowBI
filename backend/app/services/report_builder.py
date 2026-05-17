from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


REPORT_SAMPLE_SIZE = 5
HISTOGRAM_BIN_COUNT = 8
HISTOGRAM_FIELD_LIMIT = 8
FREQ_TOP_N = 20
BINNING_BINS = 10
GROUP_CARDINALITY_LIMIT = 20
VIOLIN_BINS = 30
HEATMAP_SAMPLE_ROWS = 200
SCATTER_SAMPLE_SIZE = 500
OUTLIER_MAX_SHOW = 30
TIMESERIES_DETECT_FIELDS = 5


def build_report(dataframe: pd.DataFrame) -> dict:
    dtypes = {col: str(dtype) for col, dtype in dataframe.dtypes.items()}

    missing = dataframe.isna().sum()
    missing_rate = (missing / len(dataframe)) if len(dataframe) > 0 else missing

    numeric_summary = _build_numeric_summary(dataframe)
    histograms = _build_histograms(dataframe)
    sample_rows = _build_sample_rows(dataframe)
    frequencies = _build_frequencies(dataframe)
    pareto = _build_pareto(dataframe)
    boxplot = _build_boxplot(dataframe)
    correlation = _build_correlation(dataframe)
    group_stats = _build_group_stats(dataframe)
    binning = _build_binning(dataframe)
    violin = _build_violin(dataframe)
    scatter_matrix = _build_scatter_matrix(dataframe)
    missing_heatmap = _build_missing_heatmap(dataframe)
    timeseries = _build_timeseries(dataframe)
    outliers = _build_outliers(dataframe)

    return {
        "dtypes": dtypes,
        "missing": {col: int(value) for col, value in missing.items()},
        "missing_rate": {col: _normalize_value(value) for col, value in missing_rate.items()},
        "numeric_summary": numeric_summary,
        "histograms": histograms,
        "sample_rows": sample_rows,
        "frequencies": frequencies,
        "pareto": pareto,
        "boxplot": boxplot,
        "correlation": correlation,
        "group_stats": group_stats,
        "binning": binning,
        "violin": violin,
        "scatter_matrix": scatter_matrix,
        "missing_heatmap": missing_heatmap,
        "timeseries": timeseries,
        "outliers": outliers,
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


def _build_frequencies(dataframe: pd.DataFrame) -> dict:
    categorical_cols = dataframe.select_dtypes(include="object").columns
    frequencies = {}

    for col in categorical_cols:
        series = dataframe[col].dropna()
        if series.empty:
            continue
        counts = series.value_counts().head(FREQ_TOP_N)
        frequencies[str(col)] = [
            {"value": _normalize_value(idx), "count": int(cnt)}
            for idx, cnt in counts.items()
        ]

    return frequencies


def _build_pareto(dataframe: pd.DataFrame) -> dict:
    numeric_df = dataframe.select_dtypes(include="number")
    pareto = {}

    for col in numeric_df.columns:
        series = numeric_df[col].dropna()
        if series.empty:
            continue
        sorted_vals = series.sort_values(ascending=False).reset_index(drop=True)
        total = float(sorted_vals.sum())
        cumulative = 0.0
        items = []
        for val in sorted_vals.head(FREQ_TOP_N):
            cumulative += float(val)
            items.append({
                "value": _normalize_value(val),
                "count": cumulative,
                "cum_pct": cumulative / total if total > 0 else 0.0,
            })
        pareto[str(col)] = items

    return pareto


def _build_boxplot(dataframe: pd.DataFrame) -> dict:
    numeric_df = dataframe.select_dtypes(include="number")
    boxplot = {}

    for col in numeric_df.columns:
        series = numeric_df[col].dropna()
        if series.empty:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr

        outliers = series[(series < lower_fence) | (series > upper_fence)].tolist()
        outliers = [_normalize_value(v) for v in outliers[:50]]

        boxplot[str(col)] = {
            "min": float(series.min()),
            "q1": q1,
            "median": float(series.median()),
            "q3": q3,
            "max": float(series.max()),
            "lower_fence": lower_fence,
            "upper_fence": upper_fence,
            "outliers": outliers,
            "outlier_count": len(outliers),
        }

    return boxplot


def _build_correlation(dataframe: pd.DataFrame) -> dict:
    numeric_df = dataframe.select_dtypes(include="number")
    if numeric_df.empty:
        return {"fields": [], "matrix": []}

    corr = numeric_df.corr()
    fields = [str(col) for col in corr.columns]
    matrix = []
    for _, row in corr.iterrows():
        matrix.append([_normalize_value(v) for v in row.tolist()])

    return {"fields": fields, "matrix": matrix}


def _build_group_stats(dataframe: pd.DataFrame) -> dict:
    categorical_cols = dataframe.select_dtypes(include="object").columns
    numeric_cols = dataframe.select_dtypes(include="number").columns

    result = {
        "categorical_fields": [],
        "numeric_fields": [str(c) for c in numeric_cols],
        "data": {},
    }

    for cat_col in categorical_cols:
        series = dataframe[cat_col].dropna()
        if series.nunique() > GROUP_CARDINALITY_LIMIT or series.nunique() < 2:
            continue

        result["categorical_fields"].append(str(cat_col))
        grouped = dataframe.groupby(cat_col)[numeric_cols]

        group_data = {}
        for name, group in grouped:
            label = str(name)
            stats = {}
            for num_col in numeric_cols:
                col_series = group[num_col].dropna()
                if col_series.empty:
                    continue
                stats[str(num_col)] = {
                    "mean": _normalize_value(col_series.mean()),
                    "max": _normalize_value(col_series.max()),
                    "min": _normalize_value(col_series.min()),
                }
            if stats:
                group_data[label] = stats

        if group_data:
            result["data"][str(cat_col)] = group_data

    return result


def _build_binning(dataframe: pd.DataFrame) -> dict:
    numeric_df = dataframe.select_dtypes(include="number")
    binning = {}

    for col in numeric_df.columns[:HISTOGRAM_FIELD_LIMIT]:
        series = numeric_df[col].dropna()
        if series.empty:
            continue

        unique_vals = max(1, int(series.nunique()))
        actual_bins = min(BINNING_BINS, unique_vals)

        ew_counts, ew_edges = np.histogram(series.to_numpy(), bins=actual_bins)

        ef_edges = []
        sorted_vals = series.sort_values().to_numpy()
        n = len(sorted_vals)
        ef_edges.append(float(sorted_vals[0]))
        for i in range(1, actual_bins):
            idx = int(i * n / actual_bins)
            ef_edges.append(float(sorted_vals[min(idx, n - 1)]))
        ef_edges.append(float(sorted_vals[-1]))
        ef_edges = sorted(set(ef_edges))
        if len(ef_edges) < 2:
            ef_counts, ef_edges = [], []
        else:
            ef_counts, ef_edges = np.histogram(sorted_vals, bins=ef_edges)

        binning[str(col)] = {
            "equal_width": {
                "bins": [float(v) for v in ew_edges.tolist()],
                "counts": [int(v) for v in ew_counts.tolist()],
            },
            "equal_freq": {
                "bins": [float(v) for v in ef_edges.tolist()],
                "counts": [int(v) for v in ef_counts.tolist()],
            },
        }

    return binning


def _smooth_kde(values: np.ndarray, bins: int, sigma: float = 1.0) -> tuple:
    hist, edges = np.histogram(values, bins=bins, density=True)
    kernel = np.exp(-np.linspace(-2, 2, max(3, int(bins * 0.2))) ** 2 / (2 * sigma ** 2))
    kernel = kernel / kernel.sum()
    smoothed = np.convolve(hist, kernel, mode="same")
    centers = (edges[:-1] + edges[1:]) / 2
    return centers.tolist(), smoothed.tolist()


def _build_violin(dataframe: pd.DataFrame) -> dict:
    numeric_df = dataframe.select_dtypes(include="number")
    violin = {}

    for col in numeric_df.columns[:HISTOGRAM_FIELD_LIMIT]:
        series = numeric_df[col].dropna()
        if series.empty or series.nunique() < 3:
            continue

        vals = series.to_numpy()
        centers, density = _smooth_kde(vals, VIOLIN_BINS)

        violin[str(col)] = {
            "density_x": centers,
            "density_y": density,
            "min": float(vals.min()),
            "max": float(vals.max()),
            "mean": float(vals.mean()),
        }

    return violin


def _build_scatter_matrix(dataframe: pd.DataFrame) -> dict:
    numeric_df = dataframe.select_dtypes(include="number").dropna(how="all")
    if numeric_df.empty:
        return {"fields": [], "data": []}

    limited = numeric_df.iloc[:, :6]
    if len(limited) > SCATTER_SAMPLE_SIZE:
        limited = limited.sample(n=SCATTER_SAMPLE_SIZE, random_state=42)

    fields = [str(c) for c in limited.columns]
    data = limited.dropna().head(SCATTER_SAMPLE_SIZE).to_dict(orient="records")

    for row in data:
        for k, v in row.items():
            row[k] = _normalize_value(v)

    return {"fields": fields, "data": data}


def _build_missing_heatmap(dataframe: pd.DataFrame) -> dict:
    fields = [str(c) for c in dataframe.columns]
    n_rows = len(dataframe)
    step = max(1, n_rows // HEATMAP_SAMPLE_ROWS)
    sampled = dataframe.iloc[::step, :].reset_index(drop=True) if n_rows > HEATMAP_SAMPLE_ROWS else dataframe

    missing_data = sampled.isna().values.tolist()
    cleaned = []
    for row in missing_data:
        cleaned.append([bool(v) for v in row])

    return {
        "fields": fields,
        "rows": len(cleaned),
        "total_rows": n_rows,
        "sampled": n_rows > HEATMAP_SAMPLE_ROWS,
        "data": cleaned,
    }


def _build_timeseries(dataframe: pd.DataFrame) -> dict:
    datetime_cols = dataframe.select_dtypes(include=["datetime64"]).columns
    if not len(datetime_cols):
        datetime_cols = []
        for col in dataframe.columns[:TIMESERIES_DETECT_FIELDS]:
            try:
                converted = pd.to_datetime(dataframe[col], format="mixed")
                if converted.notna().sum() > len(dataframe) * 0.5:
                    datetime_cols = [col]
                    dataframe[col] = converted
                    break
            except (ValueError, TypeError):
                continue

    result = {}
    for col in datetime_cols[:3]:
        series = pd.to_datetime(dataframe[col], format="mixed", errors="coerce").dropna()
        if series.empty:
            continue

        base = dataframe.index if col not in dataframe.columns else dataframe.index
        temp = pd.DataFrame({"date": series})
        daily = temp.set_index("date").resample("D").size()
        monthly = temp.set_index("date").resample("ME").size()
        yearly = temp.set_index("date").resample("YE").size()

        if len(daily) > 1:
            result[str(col)] = {
                "daily": {
                    "dates": [str(d.date()) for d in daily.index.tolist()],
                    "values": [int(v) for v in daily.tolist()],
                },
                "monthly": {
                    "dates": [str(d.date()) for d in monthly.index.tolist()],
                    "values": [int(v) for v in monthly.tolist()],
                },
                "yearly": {
                    "dates": [str(d.date()) for d in yearly.index.tolist()],
                    "values": [int(v) for v in yearly.tolist()],
                },
            }

    return result


def _build_outliers(dataframe: pd.DataFrame) -> dict:
    numeric_df = dataframe.select_dtypes(include="number")
    result = {}

    for col in numeric_df.columns:
        series = numeric_df[col].dropna()
        if series.empty:
            continue

        vals = series.to_numpy()
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1

        lower_iqr = q1 - 1.5 * iqr
        upper_iqr = q3 + 1.5 * iqr

        iqr_mask = (series < lower_iqr) | (series > upper_iqr)
        iqr_vals = series[iqr_mask].tolist()[:OUTLIER_MAX_SHOW]

        mean_val = float(vals.mean())
        std_val = float(vals.std()) if vals.std() > 0 else 1.0
        z_scores = np.abs((vals - mean_val) / std_val)
        zscore_mask = z_scores > 3
        zscore_vals = series[zscore_mask].tolist()[:OUTLIER_MAX_SHOW]

        result[str(col)] = {
            "iqr": {
                "count": int(iqr_mask.sum()),
                "lower_fence": lower_iqr,
                "upper_fence": upper_iqr,
                "sample_values": [_normalize_value(v) for v in iqr_vals],
            },
            "zscore": {
                "count": int(zscore_mask.sum()),
                "threshold": 3,
                "sample_values": [_normalize_value(v) for v in zscore_vals],
            },
        }

    return result


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
