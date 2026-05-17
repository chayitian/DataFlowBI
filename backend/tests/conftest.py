import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "age": [25, 30, 35, None, 28],
        "salary": [50000, 60000, 70000, 80000, None],
        "department": ["Engineering", "Sales", "Engineering", "HR", "Sales"],
        "start_date": pd.to_datetime(["2020-01-15", "2021-06-01", "2019-03-10", "2022-11-20", "2020-07-07"]),
    })


@pytest.fixture
def empty_df():
    return pd.DataFrame({"a": pd.Series(dtype="int64"), "b": pd.Series(dtype="object")})


@pytest.fixture
def numeric_only_df():
    return pd.DataFrame({
        "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        "y": [10, 20, 30, 40, 50],
        "z": [0.1, 0.2, 0.3, 0.4, 0.5],
    })
