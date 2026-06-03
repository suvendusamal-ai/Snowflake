from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

from app.core.logging import configure_logging
from app.routes.health import router as health_router
from app.routes.ingest import router as ingest_router
from app.snowflake_client import SnowflakeClient

configure_logging()
app = FastAPI(
    title="Snowflake Ingestion Control Plane",
    version="1.0.0",
    description="JWT-secured FastAPI ingress for Snowflake-only data processing and transformation.",
)

app.include_router(health_router)
app.include_router(ingest_router)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Snowflake Ingestion Control Plane",
        version="1.0.0",
        description="JWT-secured FastAPI ingress for Snowflake-only data processing and transformation.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "description": "JWT Bearer token for authentication",
        }
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/", tags=["root"])
def root() -> dict[str, str]:
    return {
        "message": "Snowflake Ingestion Control Plane is running.",
        "health_url": "/health",
        "docs_url": "/docs",
        "ingest_url": "/ingest/csv",
    }


@app.on_event("startup")
def startup_event() -> None:
    SnowflakeClient().ensure_stage_and_format()
