import logging
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from fastapi import Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.core.jwt import validate_jwt_token
from app.schemas import CSVIngestResponse
from app.snowflake_client import SnowflakeClient
from app.utils import validate_csv_file, write_upload_to_disk

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])
security = HTTPBearer()


@router.post("/csv", response_model=CSVIngestResponse)
async def ingest_csv(
    credentials: HTTPAuthorizationCredentials = Security(security),
    csv_file: UploadFile = File(...),
    schema_name: str | None = Form(None),
) -> CSVIngestResponse:
    validate_jwt_token(credentials.credentials)
    validate_csv_file(csv_file)

    # Use CSV filename (without extension) as table name
    target_table = Path(csv_file.filename).stem

    with tempfile.TemporaryDirectory(dir=str(settings.temp_upload_dir)) as temporary_directory:
        temp_path = write_upload_to_disk(csv_file, Path(temporary_directory))
        snowflake_client = SnowflakeClient()
        snowflake_client.ensure_stage_and_format()

        stage_file_name = temp_path.name
        snowflake_client.put_file_to_stage(temp_path, stage_file_name)
        rows_loaded, actions = snowflake_client.copy_into_table(
            target_table,
            stage_file_name,
            schema_name,
            local_csv_path=temp_path,
        )

        transform_action = snowflake_client.call_transform_procedure(target_table, schema_name)
        actions.append(transform_action)

    return CSVIngestResponse(
        target_table=target_table,
        schema_name=schema_name or settings.snowflake_schema,
        stage_name=settings.snowflake_stage_name,
        rows_loaded=rows_loaded,
        load_status="completed",
        transform_procedure=settings.snowflake_transform_procedure,
        actions=actions,
    )
