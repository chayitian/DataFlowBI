"""上传、历史记录（模拟 DB）、导出接口和 reload_from_cache 的测试。"""
import io
import warnings
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pandas as pd
import pytest
from fastapi import UploadFile
from sqlalchemy.exc import SQLAlchemyError

from app.main import create_app
from app.database.db import build_database_url
from app.services.file_preview import (
    DATA_CACHE,
    _compute_file_hash,
    _load_dataframe,
    _save_upload,
    clean_data,
    reload_from_cache,
)
from app.services.export_service import export_report_docx, export_report_excel
from app.services.feature_engineering import engineer_features
from app.services.ml_service import train_model


SAMPLE_CSV = b"name,age,salary\nAlice,25,50000\nBob,30,60000\n"


@pytest.fixture(autouse=True)
def clear_cache():
    DATA_CACHE.clear()
    yield
    DATA_CACHE.clear()


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob"],
        "age": [25, 30],
        "salary": [50000.0, 60000.0],
    })


def _make_csv_file(filename="test.csv") -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(SAMPLE_CSV))


class TestBuildPreview:
    def test_invalid_extension(self):
        file = _make_csv_file("test.txt")
        from app.services.file_preview import build_preview
        with pytest.raises(Exception) as exc:
            build_preview(file)
        assert "Unsupported" in str(exc.value)

    def test_no_filename(self):
        file = UploadFile(filename="", file=io.BytesIO(b""))
        from app.services.file_preview import build_preview
        with pytest.raises(Exception) as exc:
            build_preview(file)
        assert "File name" in str(exc.value)


class TestSaveAndLoad:
    def test_save_and_load_csv(self, tmp_path):
        content = b"a,b\n1,2\n3,4"
        file = UploadFile(filename="data.csv", file=io.BytesIO(content))
        saved = _save_upload(file, ".csv")
        assert saved.exists()
        assert saved.suffix == ".csv"
        df = _load_dataframe(saved, ".csv")
        assert list(df.columns) == ["a", "b"]
        assert len(df) == 2

    def test_file_hash(self, tmp_path):
        p = tmp_path / "test.csv"
        p.write_bytes(b"hello")
        h = _compute_file_hash(p)
        assert isinstance(h, str)
        assert len(h) == 64

    def test_reload_from_cache_ok(self, tmp_path, sample_df):
        p = tmp_path / "cached.csv"
        sample_df.to_csv(p, index=False)
        result = reload_from_cache(str(p), "original.csv")
        assert result["filename"] == "original.csv"
        assert result["rows"] == 2
        assert result["columns"] == 3
        assert "report" in result
        assert "filter_info" in result
        saved_name = Path(p).name
        assert saved_name in DATA_CACHE

    def test_reload_from_cache_file_missing(self):
        with pytest.raises(Exception) as exc:
            reload_from_cache("/nonexistent/path.csv", "x.csv")
        assert "not found" in str(exc.value).lower()

    def test_reload_from_cache_bad_file(self, tmp_path):
        p = tmp_path / "bad.xlsx"
        p.write_bytes(b"\x00\x01\x02\x03")
        with pytest.raises(Exception):
            reload_from_cache(str(p), "bad.xlsx")


@pytest.fixture
def seeded_cache(sample_df):
    DATA_CACHE["test_session"] = sample_df
    return "test_session"


class TestExportService:
    def test_export_docx_returns_bytes(self, seeded_cache):
        buf = export_report_docx(seeded_cache, "report.docx")
        data = buf.read()
        assert len(data) > 0
        assert isinstance(data, bytes)

    def test_export_docx_cache_miss(self):
        with pytest.raises(ValueError, match="Session expired"):
            export_report_docx("nonexistent", "report")

    def test_export_excel_returns_bytes(self, seeded_cache):
        buf = export_report_excel(seeded_cache, "report.xlsx")
        data = buf.read()
        assert len(data) > 0
        assert isinstance(data, bytes)

    def test_export_excel_cache_miss(self):
        with pytest.raises(ValueError, match="Session expired"):
            export_report_excel("nonexistent", "report")


class TestExportPdfService:
    def test_export_pdf_returns_bytes(self, seeded_cache):
        from app.services.export_service import export_report_pdf
        buf = export_report_pdf(seeded_cache, "report.pdf")
        data = buf.read()
        assert len(data) > 0
        assert data.startswith(b"%PDF")

    def test_export_pdf_cache_miss(self):
        from app.services.export_service import export_report_pdf
        with pytest.raises(ValueError, match="Session expired"):
            export_report_pdf("nonexistent", "report")


class TestExportEndpoint:
    def test_export_docx_endpoint(self, client, seeded_cache):
        resp = client.get(f"/export/docx?saved_name={seeded_cache}&filename=myreport")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        assert len(resp.content) > 0

    def test_export_docx_missing_cache(self, client):
        resp = client.get("/export/docx?saved_name=nonexistent&filename=report")
        assert resp.status_code == 404

    def test_export_excel_endpoint(self, client, seeded_cache):
        resp = client.get(f"/export/excel?saved_name={seeded_cache}&filename=myreport")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        assert len(resp.content) > 0

    def test_export_excel_missing_cache(self, client):
        resp = client.get("/export/excel?saved_name=nonexistent&filename=report")
        assert resp.status_code == 404

    def test_export_pdf_endpoint(self, client, seeded_cache):
        resp = client.get(f"/export/pdf?saved_name={seeded_cache}&filename=myreport")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "application/pdf"
        assert len(resp.content) > 0
        assert resp.content.startswith(b"%PDF")

    def test_export_pdf_missing_cache(self, client):
        resp = client.get("/export/pdf?saved_name=nonexistent&filename=report")
        assert resp.status_code == 404


class TestUploadEndpoint:
    def test_upload_csv_success(self, client, tmp_path):
        from app.services.file_preview import UPLOADS_DIR
        csv_content = b"name,age\nAlice,25\nBob,30\n"
        resp = client.post(
            "/upload",
            files={"file": ("test.csv", csv_content, "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "test.csv"
        assert data["rows"] == 2
        assert data["columns"] == 2
        assert "saved_name" in data
        assert "report" in data
        assert "filter_info" in data

    def test_upload_invalid_extension(self, client):
        resp = client.post(
            "/upload",
            files={"file": ("test.txt", b"hello", "text/plain")},
        )
        assert resp.status_code == 400
        assert "Unsupported" in resp.json()["detail"]

    def test_upload_empty_filename(self, client):
        resp = client.post(
            "/upload",
            files={"file": ("", b"data", "text/csv")},
        )
        assert resp.status_code in (400, 422)

    def test_upload_malformed_csv(self, client):
        resp = client.post(
            "/upload",
            files={"file": ("bad.csv", b"\xff\xfe\x00\x01", "text/csv")},
        )
        assert resp.status_code == 400
    def test_upload_large_file(self, client):
        import sys
        from app.services.file_preview import build_preview
        big = b"x" * (100 * 1024 * 1024 + 1)
        resp = client.post(
            "/upload",
            files={"file": ("big.csv", big, "text/csv")},
            headers={"content-length": str(len(big))},
        )
        assert resp.status_code == 413


class TestCleanData:
    def test_clean_drop_missing(self, seeded_cache):
        DATA_CACHE[seeded_cache] = pd.DataFrame({
            "name": ["Alice", "Bob", None],
            "age": [25, None, 35],
        })
        result = clean_data(seeded_cache, missing_handling={"name": {"method": "drop"}})
        assert result["rows"] == 2
        assert any(log["operation"] == "missing_handling" for log in result["cleaning_log"])

    def test_clean_fill_mean(self, seeded_cache):
        DATA_CACHE[seeded_cache] = pd.DataFrame({
            "value": [1.0, 2.0, None, 4.0],
        })
        result = clean_data(seeded_cache, missing_handling={"value": {"method": "fill_mean"}})
        assert result["rows"] == 4
        df = DATA_CACHE[seeded_cache]
        assert df["value"].isna().sum() == 0
        assert df["value"].iloc[2] == pytest.approx(7.0 / 3, rel=1e-3)

    def test_clean_fill_value(self, seeded_cache):
        DATA_CACHE[seeded_cache] = pd.DataFrame({
            "label": ["a", None, "c"],
        })
        result = clean_data(seeded_cache, missing_handling={"label": {"method": "fill_value", "value": "unknown"}})
        df = DATA_CACHE[seeded_cache]
        assert df["label"].iloc[1] == "unknown"

    def test_clean_iqr_remove(self, seeded_cache):
        DATA_CACHE[seeded_cache] = pd.DataFrame({
            "value": [1, 2, 3, 4, 5, 100],
        })
        result = clean_data(seeded_cache, outlier_handling={"value": {"method": "iqr", "threshold": 1.5, "action": "remove"}})
        assert result["rows"] == 5
        assert any(log["operation"] == "outlier_handling" for log in result["cleaning_log"])

    def test_clean_zscore_cap(self, seeded_cache):
        DATA_CACHE[seeded_cache] = pd.DataFrame({
            "value": [10, 20, 20, 20, 30, 200],
        })
        result = clean_data(seeded_cache, outlier_handling={"value": {"method": "zscore", "threshold": 2, "action": "cap"}})
        assert result["rows"] == 6

    def test_clean_type_conversion(self, seeded_cache):
        DATA_CACHE[seeded_cache] = pd.DataFrame({
            "num_str": ["1", "2", "3"],
        })
        result = clean_data(seeded_cache, type_conversions={"num_str": "int"})
        df = DATA_CACHE[seeded_cache]
        assert str(df["num_str"].dtype) in ("Int64", "int64")

    def test_clean_cache_miss(self):
        with pytest.raises(Exception) as exc:
            clean_data("nonexistent")
        assert "expired" in str(exc.value).lower() or "not found" in str(exc.value).lower()

    def test_clean_endpoint(self, client, seeded_cache):
        resp = client.post("/clean", json={
            "saved_name": seeded_cache,
            "missing_handling": {"name": {"method": "drop"}},
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "cleaning_log" in data
        assert data["rows"] == 2


class TestFeatureEngineering:
    def test_engineer_features_creates_new_columns(self, seeded_cache):
        DATA_CACHE[seeded_cache] = pd.DataFrame({
            "age": [25, 30, 35],
            "dept": ["Engineering", "Sales", "Engineering"],
            "start_date": ["2020-01-01", "2021-02-03", "2022-03-04"],
            "target": [1, 2, 3],
        })

        result = engineer_features(
            seeded_cache,
            numeric_transforms={"age": "standardize"},
            categorical_fields=["dept"],
            datetime_fields=["start_date"],
        )

        assert "age_standardized" in result["fields"]
        assert "dept_Engineering" in result["fields"]
        assert "start_date_year" in result["fields"]
        assert result["columns"] > 4
        assert result["saved_name"] in DATA_CACHE
        assert any(log["operation"] == "numeric_transform" for log in result["feature_engineering_log"])

    def test_engineer_features_requires_operation(self, seeded_cache):
        DATA_CACHE[seeded_cache] = pd.DataFrame({"age": [25, 30, 35]})
        with pytest.raises(Exception) as exc:
            engineer_features(seeded_cache)
        assert "feature engineering" in str(exc.value).lower()


class TestMLFeatureNames:
    def test_coefficients_use_display_feature_names(self):
        df = pd.DataFrame({
            "age": [20, 25, 30, 35, 40, 45, 50, 55],
            "bmi": [18.5, 19.0, 21.2, 22.5, 24.0, 26.1, 28.3, 30.0],
            "target": [80, 90, 110, 125, 140, 155, 170, 190],
        })

        result = train_model(
            df=df,
            task_type="regression",
            target="target",
            features=["age", "bmi"],
            split_strategy="random",
            test_size=0.25,
            val_size=None,
            time_column=None,
            model_type="linear",
            params={},
        )

        feature_names = [row["feature"] for row in result["coefficients"]]
        assert feature_names == ["age", "bmi"]

    def test_categorical_coefficients_use_readable_names(self):
        df = pd.DataFrame({
            "dept": ["A", "B", "A", "B", "C", "C", "A", "B"],
            "target": [1.0, 2.0, 1.2, 2.1, 3.0, 3.1, 1.1, 2.2],
        })

        result = train_model(
            df=df,
            task_type="regression",
            target="target",
            features=["dept"],
            split_strategy="random",
            test_size=0.25,
            val_size=None,
            time_column=None,
            model_type="ridge",
            params={},
        )

        feature_names = [row["feature"] for row in result["coefficients"]]
        assert "dept=A" in feature_names
        assert all(not name.startswith("cat__") for name in feature_names)

    def test_random_forest_regressor_returns_feature_importance(self):
        df = pd.DataFrame({
            "age": [20, 25, 30, 35, 40, 45, 50, 55, 60, 65],
            "bmi": [18, 19, 20, 22, 24, 25, 26, 28, 29, 31],
            "target": [80, 90, 100, 120, 135, 150, 165, 180, 195, 210],
        })

        result = train_model(
            df=df,
            task_type="regression",
            target="target",
            features=["age", "bmi"],
            split_strategy="random",
            test_size=0.2,
            val_size=None,
            time_column=None,
            model_type="random_forest_regressor",
            params={"n_estimators": 5, "max_depth": 3, "random_state": 1},
        )

        assert result["feature_importances"]
        assert {row["feature"] for row in result["feature_importances"]} == {"age", "bmi"}

    def test_decision_tree_classifier_with_params(self):
        df = pd.DataFrame({
            "x1": [0, 0, 1, 1, 2, 2, 3, 3, 4, 4],
            "x2": [1, 2, 1, 2, 1, 2, 1, 2, 1, 2],
            "target": ["a", "a", "a", "a", "b", "b", "b", "b", "b", "b"],
        })

        result = train_model(
            df=df,
            task_type="classification",
            target="target",
            features=["x1", "x2"],
            split_strategy="random",
            test_size=0.2,
            val_size=None,
            time_column=None,
            model_type="decision_tree_classifier",
            params={"max_depth": 2, "criterion": "gini"},
        )

        assert result["feature_importances"]
        assert "accuracy" in result["metrics"]["test"]

    def test_logistic_models_do_not_emit_penalty_warnings(self):
        df = pd.DataFrame({
            "x1": list(range(20)),
            "x2": [v % 3 for v in range(20)],
            "target": ["a"] * 10 + ["b"] * 10,
        })

        for model_type in ("logistic_l2", "logistic_l1", "logistic_elasticnet"):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                result = train_model(
                    df=df,
                    task_type="classification",
                    target="target",
                    features=["x1", "x2"],
                    split_strategy="random",
                    test_size=0.2,
                    val_size=None,
                    time_column=None,
                    model_type=model_type,
                    params={"max_iter": 2000, "l1_ratio": 0.5},
                )

            messages = [str(warning.message) for warning in caught]
            assert "accuracy" in result["metrics"]["test"]
            assert not any("penalty" in message and "deprecated" in message for message in messages)
            assert not any("Inconsistent values" in message for message in messages)


class TestDatabaseConfig:
    def test_build_postgres_url_from_env(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("POSTGRES_HOST", "localhost")
        monkeypatch.setenv("POSTGRES_PORT", "5432")
        monkeypatch.setenv("POSTGRES_USER", "postgres")
        monkeypatch.setenv("POSTGRES_PASSWORD", "123456")
        monkeypatch.setenv("POSTGRES_DB", "dataflowbi")

        url = build_database_url()

        assert url.drivername == "postgresql+psycopg"
        assert url.username == "postgres"
        assert url.password == "123456"
        assert url.host == "localhost"
        assert url.port == 5432
        assert url.database == "dataflowbi"

    def test_database_url_override(self, monkeypatch):
        value = "postgresql+psycopg://postgres:123456@localhost:5432/dataflowbi"
        monkeypatch.setenv("DATABASE_URL", value)

        assert build_database_url() == value


class TestHistoryEndpoint:
    @patch("app.api.history.SessionLocal")
    def test_list_history_empty(self, mock_session, client):
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 0
        mock_db.query.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_session.return_value = mock_db
        resp = client.get("/history")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["records"] == []

    @patch("app.api.history.SessionLocal")
    def test_list_history_db_unavailable_degrades_to_empty(self, mock_session, client):
        mock_db = MagicMock()
        mock_db.query.side_effect = SQLAlchemyError("database down")
        mock_session.return_value = mock_db

        resp = client.get("/history")

        assert resp.status_code == 200
        assert resp.json() == {"records": [], "total": 0}

    @patch("app.api.history.SessionLocal")
    def test_history_detail_db_unavailable_returns_503(self, mock_session, client):
        mock_db = MagicMock()
        mock_db.query.side_effect = SQLAlchemyError("database down")
        mock_session.return_value = mock_db

        resp = client.get("/history/1")

        assert resp.status_code == 503

    @patch("app.api.history.SessionLocal")
    def test_get_history_detail_not_found(self, mock_session, client):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session.return_value = mock_db
        resp = client.get("/history/999")
        assert resp.status_code == 404

    @patch("app.api.history.SessionLocal")
    def test_reload_history_not_found(self, mock_session, client):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_session.return_value = mock_db
        resp = client.post("/history/999/reload")
        assert resp.status_code == 404

    @patch("app.api.history.SessionLocal")
    def test_reload_history_success(self, mock_session, client, tmp_path):
        df = pd.DataFrame({"a": [1, 2]})
        p = tmp_path / "cached.csv"
        df.to_csv(p, index=False)

        from app.models.upload_record import UploadRecord
        mock_record = MagicMock(spec=UploadRecord)
        mock_record.id = 1
        mock_record.filename = p.name
        mock_record.original_filename = "original.csv"
        mock_record.file_size = 100
        mock_record.file_hash = "abc"
        mock_record.row_count = 2
        mock_record.column_count = 1
        mock_record.columns_json = ["a"]
        mock_record.dtypes_json = '{"a": "int64"}'
        mock_record.cached_path = str(p)
        mock_record.created_at = "2024-01-01T00:00:00"

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_record
        mock_session.return_value = mock_db

        resp = client.post("/history/1/reload")
        assert resp.status_code == 200
        data = resp.json()
        assert data["filename"] == "original.csv"
        assert data["rows"] == 2
        assert data["columns"] == 1
