import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True, scope="session")
def set_test_env():
    """Set test environment variables before any imports."""
    os.environ["JWT_SECRET_KEY"] = "testsecret"
    os.environ["JWT_ALGORITHM"] = "HS256"
    os.environ["JWT_AUDIENCE"] = "test-audience"
    os.environ["JWT_ISSUER"] = "test-issuer"
    os.environ["SNOWFLAKE_USER"] = "test_user"
    os.environ["SNOWFLAKE_PASSWORD"] = "test_password"
    os.environ["SNOWFLAKE_ACCOUNT"] = "test_account"
    os.environ["SNOWFLAKE_WAREHOUSE"] = "test_warehouse"
    os.environ["SNOWFLAKE_DATABASE"] = "TEST_DB"
    os.environ["SNOWFLAKE_SCHEMA"] = "PUBLIC"
    os.environ["SNOWFLAKE_ROLE"] = "SYSADMIN"


@pytest.fixture(scope="session")
def client() -> TestClient:
    from app.main import app

    return TestClient(app)
    monkeypatch.setattr("app.main.SnowflakeClient", lambda: mock_snowflake_client)
