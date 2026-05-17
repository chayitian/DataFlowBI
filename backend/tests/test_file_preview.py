import pandas as pd
import pytest
from fastapi import HTTPException

from app.services.file_preview import (
    DATA_CACHE,
    build_filter_info,
    filter_data,
    rebin_histogram,
)


@pytest.fixture(autouse=True)
def clear_cache():
    DATA_CACHE.clear()
    yield
    DATA_CACHE.clear()


@pytest.fixture
def seeded_cache():
    df = pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie"],
        "age": [25, 30, 35],
        "salary": [50000.0, 60000.0, 70000.0],
        "dept": ["Engineering", "Sales", "Engineering"],
    })
    DATA_CACHE["test_session"] = df
    return "test_session"


class TestRebinHistogram:
    def test_basic(self, seeded_cache):
        result = rebin_histogram(seeded_cache, "age", 3, False)
        assert result["field"] == "age"
        assert result["bin_count"] == 3
        assert result["normalize"] is False
        assert len(result["bins"]) == len(result["counts"]) + 1
        assert all(isinstance(c, int) for c in result["counts"])

    def test_normalize(self, seeded_cache):
        result = rebin_histogram(seeded_cache, "age", 3, True)
        assert result["normalize"] is True
        assert all(isinstance(c, float) for c in result["counts"])
        assert abs(sum(result["counts"]) - 1.0) < 1e-6

    def test_cache_miss(self):
        with pytest.raises(HTTPException) as exc:
            rebin_histogram("nonexistent", "age", 5, False)
        assert exc.value.status_code == 404
        assert "Session expired" in exc.value.detail

    def test_field_not_found(self, seeded_cache):
        with pytest.raises(HTTPException) as exc:
            rebin_histogram(seeded_cache, "not_a_column", 5, False)
        assert exc.value.status_code == 400
        assert "not found" in exc.value.detail.lower()

    def test_not_numeric(self, seeded_cache):
        with pytest.raises(HTTPException) as exc:
            rebin_histogram(seeded_cache, "name", 5, False)
        assert exc.value.status_code == 400
        assert "not numeric" in exc.value.detail.lower()

    def test_empty_series(self, seeded_cache):
        df_empty = pd.DataFrame({"x": pd.Series(dtype="float64")})
        DATA_CACHE["empty_session"] = df_empty
        with pytest.raises(HTTPException) as exc:
            rebin_histogram("empty_session", "x", 5, False)
        assert exc.value.status_code == 400
        assert "no data" in exc.value.detail.lower()

    def test_bin_count_clamped(self, seeded_cache):
        result = rebin_histogram(seeded_cache, "age", 100, False)
        assert result["bin_count"] == 3


class TestFilterData:
    def test_basic(self, seeded_cache):
        result = filter_data(seeded_cache)
        assert result["rows"] == 3
        assert result["columns"] == 4
        assert "report" in result

    def test_include_fields(self, seeded_cache):
        result = filter_data(seeded_cache, include_fields=["name", "age"])
        assert result["columns"] == 2
        assert result["rows"] == 3
        assert "name" in result["fields"]
        assert "age" in result["fields"]
        assert "salary" not in result["fields"]

    def test_include_fields_ignores_missing(self, seeded_cache):
        result = filter_data(seeded_cache, include_fields=["name", "nonexistent"])
        assert result["columns"] == 1
        assert "name" in result["fields"]

    def test_numeric_ranges(self, seeded_cache):
        result = filter_data(seeded_cache, numeric_ranges={"age": [28, 35]})
        assert result["rows"] == 2

    def test_numeric_ranges_all_excluded(self, seeded_cache):
        result = filter_data(seeded_cache, numeric_ranges={"age": [100, 200]})
        assert result["rows"] == 0

    def test_categorical_values(self, seeded_cache):
        result = filter_data(seeded_cache, categorical_values={"dept": ["Engineering"]})
        assert result["rows"] == 2
        assert result["columns"] == 4

    def test_categorical_values_empty_result(self, seeded_cache):
        result = filter_data(seeded_cache, categorical_values={"dept": ["Nonexistent"]})
        assert result["rows"] == 0

    def test_cache_miss(self):
        with pytest.raises(HTTPException) as exc:
            filter_data("nonexistent")
        assert exc.value.status_code == 404

    def test_numeric_range_on_non_numeric_field(self, seeded_cache):
        result = filter_data(seeded_cache, numeric_ranges={"name": [1, 10]})
        assert result["rows"] == 3


class TestBuildFilterInfo:
    def test_basic(self, sample_df):
        info = build_filter_info(sample_df)
        assert "name" in info
        assert "age" in info
        assert info["name"]["dtype"] == "object"
        assert "values" in info["name"]
        assert len(info["name"]["values"]) == 5
        assert info["age"]["dtype"].startswith("float")
        assert "min" in info["age"]
        assert "max" in info["age"]
        assert "mean" in info["age"]

    def test_numeric_stats(self):
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0]})
        info = build_filter_info(df)
        assert info["x"]["min"] == 1.0
        assert info["x"]["max"] == 3.0
        assert info["x"]["mean"] == 2.0

    def test_empty_dataframe(self, empty_df):
        info = build_filter_info(empty_df)
        assert "a" in info
        assert "b" in info
