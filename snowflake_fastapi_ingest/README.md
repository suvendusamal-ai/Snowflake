# Snowflake FastAPI Ingestion Control Plane

This repository provides a production-grade pattern for a JWT-secured FastAPI ingress/egress control plane that keeps all business logic, data transformation, and inference inside Snowflake.

## Architecture Overview

- FastAPI receives authenticated requests and validates JWT tokens.
- Ingested CSV files are uploaded to a Snowflake internal stage.
- Snowflake `COPY INTO` plus stored procedures/tasks handle all transformation and inference.
- FastAPI exposes secure control plane APIs only; no business rules or data processing execute outside Snowflake.

## Key design principles

- `app/` contains only authentication, request validation, routing, and Snowflake orchestration.
- `SnowflakeClient` issues SQL and file upload commands; all schema transformation stays in Snowflake.
- Optional Snowflake stored procedures or tasks implement downstream logic.
- Sensitive credentials are provided through environment variables.

## Repository structure

- `app/` - FastAPI application modules
- `tests/` - unit and integration test scaffolding
- `.env.example` - required environment variables
- `Dockerfile` - container package for deployment
- `requirements.txt` - Python dependencies

## Running locally

1. Copy `.env.example` to `.env` and populate Snowflake credentials.
2. Provision Snowflake database objects once by running `setup.sql`:

```bash
snowsql -f setup.sql
```

3. Install dependencies:

```bash
python -m pip install -r requirements.txt
```

4. Run the app:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Snowflake responsibilities

- Create the target schema/table.
- Define a `FILE FORMAT` for CSV.
- Provide a Snowflake internal stage or let the app create one.
- Implement transformation and inference logic in stored procedures, tasks, and views.

## Ingestion flow

1. Client uploads CSV to `POST /ingest/csv`.
2. FastAPI validates JWT and request parameters.
3. FastAPI writes file to a temporary file and `PUT`s it into Snowflake stage.
4. FastAPI executes `COPY INTO` to load the target table.
5. Optional Snowflake procedure is called for transformation or lineage capture.
