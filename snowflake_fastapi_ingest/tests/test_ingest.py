import os
from unittest.mock import patch

import jwt
from fastapi import status


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "ok"


@patch("app.routes.ingest.SnowflakeClient")
def test_ingest_csv_calls_snowflake(mock_snowflake_client, client):
    mock_client = mock_snowflake_client.return_value
    mock_client.copy_into_table.return_value = (42, [
        "Extracted CSV header names: id, name",
        "Derived table column names from the CSV header row.",
        "Created target table using inferred types and header-based column names.",
        "Copied staged CSV into table DEMODB.ATLAS.DATA. Rows loaded: 42.",
        "Starting Snowpark DataFrame transformations.",
        "Trimming whitespace from string columns: name",
        "Added 'loaded_at' timestamp column with current timestamp.",
        "Snowpark DataFrame transformations completed.",
        "Saved transformed DataFrame back to the target table."
    ])
    mock_client.call_transform_procedure.return_value = "No transform procedure configured."

    payload = {
        "sub": "test-user",
        "aud": os.environ["JWT_AUDIENCE"],
        "iss": os.environ["JWT_ISSUER"],
    }
    token = jwt.encode(payload, os.environ["JWT_SECRET_KEY"], algorithm=os.environ["JWT_ALGORITHM"])

    # No target_table parameter - table name derived from filename
    data = {}
    files = {"csv_file": ("data.csv", "id,name\n1,Alice\n", "text/csv")}

    response = client.post(
        "/ingest/csv",
        data=data,
        files=files,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert payload["target_table"] == "data"  # Table name derived from filename
    assert payload["rows_loaded"] == 42
    assert payload["actions"] == [
        "Extracted CSV header names: id, name",
        "Derived table column names from the CSV header row.",
        "Created target table using inferred types and header-based column names.",
        "Copied staged CSV into table DEMODB.ATLAS.DATA. Rows loaded: 42.",
        "Starting Snowpark DataFrame transformations.",
        "Trimming whitespace from string columns: name",
        "Added 'loaded_at' timestamp column with current timestamp.",
        "Snowpark DataFrame transformations completed.",
        "Saved transformed DataFrame back to the target table.",
        "No transform procedure configured."
    ]
    mock_client.ensure_stage_and_format.assert_called_once()
    mock_client.put_file_to_stage.assert_called_once()
    mock_client.copy_into_table.assert_called_once()
