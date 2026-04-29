# Architecture: JWT-Secured CSV Ingestion into Snowflake

## Goal
Keep all data ingestion, transformation, and inference inside Snowflake. FastAPI acts only as a secure control plane for:

- authentication and authorization
- CSV ingestion orchestration
- execution of Snowflake SQL control commands
- lightweight status and health endpoints

## Flow

1. Client calls `POST /ingest/csv` with:
   - Bearer JWT token
   - optional `schema_name`
   - CSV file upload
2. FastAPI verifies JWT and request fields.
3. FastAPI automatically derives the table name from the CSV filename (without extension).
4. FastAPI writes the uploaded CSV to a temporary path.
5. FastAPI uploads the file to a Snowflake internal stage using `PUT`.
6. FastAPI uses Snowflake `COPY INTO` to load the CSV into the target table.
7. If configured, FastAPI invokes a Snowflake stored procedure for downstream transformation.
8. All business logic, transformations, and inference remain inside Snowflake.

## Snowflake responsibilities

- expose an internal stage and file format
- define target schema and table structures
- implement stored procedures, views, tasks, and materialized views
- perform all transformation / inference with SQL, UDFs, or Snowpark stored procedures

## Control plane boundaries

- FastAPI does not parse or transform CSV rows.
- FastAPI does not apply business rules.
- The only non-Snowflake processing is auth validation and secure file staging.

## Recommended Snowflake pattern

- `CREATE FILE FORMAT` for CSV ingestion
- `CREATE STAGE` for inbound files
- `COPY INTO` to land raw data into a staging table
- `CALL` stored procedures to move from raw staging to curated/historical tables
- `CREATE TASK` to automate asynchronous processing if needed

## Security

- JWT tokens authenticate clients.
- environment variables store Snowflake credentials.
- app container runs with no direct database transformation logic.
- client-facing API remains a thin ingress/egress layer.
