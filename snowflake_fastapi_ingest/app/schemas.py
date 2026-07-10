from pydantic import BaseModel


class CSVIngestResponse(BaseModel):
    target_table: str
    schema_name: str
    stage_name: str
    rows_loaded: int
    load_status: str
    transform_procedure: str | None = None
    actions: list[str]


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0"
