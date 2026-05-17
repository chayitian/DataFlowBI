import pandas as pd

from app.services.report_builder import build_report


class TestBuildReport:
    def test_basic_report_structure(self, sample_df):
        report = build_report(sample_df)

        assert "dtypes" in report
        assert "missing" in report
        assert "missing_rate" in report
        assert "numeric_summary" in report
        assert "histograms" in report
        assert "sample_rows" in report
        assert "frequencies" in report
        assert "pareto" in report
        assert "boxplot" in report
        assert "correlation" in report
        assert "group_stats" in report
        assert "binning" in report
        assert "violin" in report
        assert "scatter_matrix" in report
        assert "missing_heatmap" in report
        assert "timeseries" in report
        assert "outliers" in report

    def test_dtypes(self, sample_df):
        report = build_report(sample_df)
        assert report["dtypes"]["name"] == "object"
        assert report["dtypes"]["age"].startswith("float")
        assert report["dtypes"]["salary"].startswith("float")
        assert report["dtypes"]["department"] == "object"
        assert report["dtypes"]["start_date"].startswith("datetime")

    def test_missing_counts(self, sample_df):
        report = build_report(sample_df)
        assert report["missing"]["name"] == 0
        assert report["missing"]["age"] == 1
        assert report["missing"]["salary"] == 1

    def test_missing_rate(self, sample_df):
        report = build_report(sample_df)
        assert report["missing_rate"]["age"] == 0.2
        assert report["missing_rate"]["salary"] == 0.2
        assert report["missing_rate"]["name"] == 0.0

    def test_numeric_summary(self, sample_df):
        report = build_report(sample_df)
        ns = report["numeric_summary"]
        assert "age" in ns
        assert "salary" in ns
        assert ns["age"]["count"] == 4
        assert ns["age"]["mean"] == 29.5
        assert ns["age"]["min"] == 25.0
        assert ns["age"]["max"] == 35.0

    def test_sample_rows(self, sample_df):
        report = build_report(sample_df)
        assert len(report["sample_rows"]) == 5
        for row in report["sample_rows"]:
            assert "name" in row
            assert "age" in row

    def test_frequencies(self, sample_df):
        report = build_report(sample_df)
        freqs = report["frequencies"]
        assert "name" in freqs
        assert "department" in freqs
        dept_vals = {d["value"]: d["count"] for d in freqs["department"]}
        assert dept_vals.get("Engineering") == 2

    def test_correlation(self, sample_df):
        report = build_report(sample_df)
        corr = report["correlation"]
        assert "fields" in corr
        assert "matrix" in corr
        assert len(corr["fields"]) == 2
        assert "age" in corr["fields"]

    def test_histograms(self, sample_df):
        report = build_report(sample_df)
        hist = report["histograms"]
        assert "age" in hist
        assert "salary" in hist
        assert "bins" in hist["age"]
        assert "counts" in hist["age"]
        assert len(hist["age"]["bins"]) == len(hist["age"]["counts"]) + 1

    def test_boxplot(self, sample_df):
        report = build_report(sample_df)
        bp = report["boxplot"]
        assert "age" in bp
        assert bp["age"]["q1"] <= bp["age"]["median"] <= bp["age"]["q3"]

    def test_empty_dataframe(self, empty_df):
        report = build_report(empty_df)
        assert report["dtypes"]["a"] == "int64"
        assert report["numeric_summary"] == {}
        assert report["sample_rows"] == []
        assert report["correlation"] == {"fields": [], "matrix": []}
        assert report["missing_heatmap"] == {
            "fields": ["a", "b"],
            "rows": 0,
            "total_rows": 0,
            "sampled": False,
            "data": [],
        }

    def test_numeric_only(self, numeric_only_df):
        report = build_report(numeric_only_df)
        assert report["frequencies"] == {}
        ns = report["numeric_summary"]
        assert "x" in ns
        assert "y" in ns
        assert "z" in ns
        assert report["correlation"]["fields"] == ["x", "y", "z"]

    def test_all_nan_column(self):
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "val": pd.Series([None, None, None], dtype="float64"),
            "label": ["a", "b", "c"],
        })
        report = build_report(df)
        assert report["numeric_summary"]["val"]["count"] == 0
        assert report["numeric_summary"]["val"]["mean"] is None
        assert "val" not in report["histograms"]
        assert "val" not in report["boxplot"]

    def test_timeseries_detection(self, sample_df):
        report = build_report(sample_df)
        ts = report["timeseries"]
        assert "start_date" in ts
        assert "daily" in ts["start_date"]
        assert len(ts["start_date"]["daily"]["dates"]) > 1
        assert "monthly" in ts["start_date"]
        assert "yearly" in ts["start_date"]

    def test_outliers(self, sample_df):
        report = build_report(sample_df)
        out = report["outliers"]
        assert "age" in out
        assert "salary" in out
        assert "iqr" in out["age"]
        assert "zscore" in out["age"]
        assert "count" in out["age"]["iqr"]
        assert "sample_values" in out["age"]["zscore"]

    def test_pareto(self, sample_df):
        report = build_report(sample_df)
        pareto = report["pareto"]
        assert "age" in pareto
        assert "salary" in pareto
        assert len(pareto["age"]) > 0
        for item in pareto["age"]:
            assert "value" in item
            assert "count" in item
            assert "cum_pct" in item
