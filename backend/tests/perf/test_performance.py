import os
import time

import pandas as pd
import pytest

from app.services.file_preview import DATA_CACHE, clean_data
from app.services.report_builder import build_report


def _should_run_perf():
    return os.getenv("PERF_TESTS", "0") == "1"


@pytest.mark.performance
def test_build_report_performance():
    if not _should_run_perf():
        pytest.skip("Set PERF_TESTS=1 to run performance tests.")

    rows = 20000
    df = pd.DataFrame({
        "age": range(rows),
        "salary": [50000 + (i % 1000) for i in range(rows)],
        "dept": ["Eng" if i % 2 == 0 else "Sales" for i in range(rows)],
        "score": [float(i % 100) for i in range(rows)],
    })

    start = time.monotonic()
    report = build_report(df)
    duration = time.monotonic() - start

    assert report["numeric_summary"]
    assert duration < 10.0


@pytest.mark.performance
def test_clean_data_performance(tmp_path):
    if not _should_run_perf():
        pytest.skip("Set PERF_TESTS=1 to run performance tests.")

    rows = 15000
    df = pd.DataFrame({
        "age": [float(i % 100) for i in range(rows)],
        "salary": [50000 + (i % 2000) for i in range(rows)],
        "dept": ["Eng" if i % 2 == 0 else "Sales" for i in range(rows)],
    })
    df.loc[::50, "age"] = None
    DATA_CACHE["perf_session"] = df

    start = time.monotonic()
    result = clean_data(
        "perf_session",
        missing_handling={"age": {"method": "fill_mean"}},
        outlier_handling={"salary": {"method": "iqr", "threshold": 1.5, "action": "cap"}},
        type_conversions={"age": "float"},
    )
    duration = time.monotonic() - start

    assert result["rows"] == rows
    assert duration < 12.0
