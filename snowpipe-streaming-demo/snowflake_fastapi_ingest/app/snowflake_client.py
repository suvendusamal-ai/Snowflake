import csv
import logging
from pathlib import Path
from typing import Any

import snowflake.connector
from snowflake.connector import SnowflakeConnection
from snowflake.snowpark import Session, functions as F
from snowflake.snowpark.dataframe import DataFrame

from app.config import settings

logger = logging.getLogger(__name__)


def quote_identifier(identifier: str) -> str:
    normalized = identifier.upper()
    return '"' + normalized.replace('"', '""') + '"'


def quote_identifier_preserve_case(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


class SnowflakeClient:
    def __init__(self) -> None:
        self._connection: SnowflakeConnection | None = None
        self._snowpark_session: Session | None = None

    def get_snowpark_session(self) -> Session:
        if self._snowpark_session is None:
            self._snowpark_session = Session.builder.configs(self._session_config()).create()
        return self._snowpark_session

    def _session_config(self) -> dict[str, str]:
        return {
            "user": settings.snowflake_user,
            "password": settings.snowflake_password.get_secret_value(),
            "account": settings.snowflake_account,
            "warehouse": settings.snowflake_warehouse,
            "database": settings.snowflake_database,
            "schema": settings.snowflake_schema,
            "role": settings.snowflake_role,
            "client_session_keep_alive": "true",
        }

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> list[tuple[Any, ...]]:
        conn = self.connect()
        with conn.cursor() as cursor:
            logger.debug("Executing SQL: %s", sql)
            cursor.execute(sql, params or {})
            try:
                return cursor.fetchall()
            except snowflake.connector.errors.ProgrammingError:
                return []

    def ensure_stage_and_format(self) -> None:
        stage_name = settings.snowflake_stage_name
        file_format_name = settings.snowflake_file_format

        stage_sql = f"SHOW STAGES LIKE '{stage_name}'"
        file_format_sql = f"SHOW FILE FORMATS LIKE '{file_format_name}'"

        with self.connect().cursor() as cursor:
            logger.info("Validating Snowflake file format and internal stage exist")
            cursor.execute(stage_sql)
            stages = cursor.fetchall()
            cursor.execute(file_format_sql)
            file_formats = cursor.fetchall()

        if not stages:
            raise RuntimeError(
                "Snowflake stage is not available. "
                f"Create stage '{stage_name}' once using setup.sql before starting the app."
            )

        if not file_formats:
            raise RuntimeError(
                "Snowflake file format is not available. "
                f"Create file format '{file_format_name}' once using setup.sql before starting the app."
            )

        logger.info(
            "Verified pre-created stage '%s' and file format '%s'.",
            stage_name,
            file_format_name,
        )

    def put_file_to_stage(self, file_path: Path, stage_file_name: str) -> str:
        stage_name = quote_identifier(settings.snowflake_stage_name)
        put_sql = f"PUT file://{file_path.as_posix()} @{stage_name} AUTO_COMPRESS=FALSE OVERWRITE=TRUE"

        with self.connect().cursor() as cursor:
            logger.info("Uploading file to Snowflake stage: %s", stage_file_name)
            cursor.execute(put_sql)
            return stage_file_name

    def copy_into_table(
        self,
        target_table: str,
        stage_file_name: str,
        schema_name: str | None = None,
        local_csv_path: Path | None = None,
    ) -> tuple[int, list[str]]:
        schema_name = schema_name or settings.snowflake_schema
        stage_name = quote_identifier(settings.snowflake_stage_name)
        target_table_name = quote_identifier(target_table)
        escape_schema = quote_identifier(schema_name)
        escape_db = quote_identifier(settings.snowflake_database)

        full_table_name = f"{escape_db}.{escape_schema}.{target_table_name}"
        actions: list[str] = []

        header_names: list[str] | None = None
        if local_csv_path is not None:
            header_names = self._read_csv_header(local_csv_path)
            actions.append(
                f"Extracted CSV header names: {', '.join(header_names)}"
            )

        with self.connect().cursor() as cursor:
            logger.info("Creating/replacing table %s with inferred schema from CSV.", full_table_name)
            
            schema_sql = f"""
                SELECT COLUMN_NAME, TYPE
                FROM TABLE(
                    INFER_SCHEMA(
                        LOCATION => '@{stage_name}/{stage_file_name}',
                        FILE_FORMAT => '{settings.snowflake_file_format}'
                    )
                )
                ORDER BY ORDER_ID
            """
            cursor.execute(schema_sql)
            columns = cursor.fetchall()
            
            if columns:
                if header_names and len(header_names) == len(columns):
                    column_names = header_names
                    actions.append(
                        "Derived table column names from the CSV header row."
                    )
                elif header_names:
                    column_names = [col[0] for col in columns]
                    actions.append(
                        "CSV header row could not be applied because header count did not match inferred column count."
                    )
                else:
                    column_names = [col[0] for col in columns]

                col_definitions = ", ".join(
                    [
                        f"{quote_identifier_preserve_case(column_names[i])} {columns[i][1]}"
                        for i in range(len(columns))
                    ]
                )
                create_table_sql = f"CREATE OR REPLACE TABLE {full_table_name} ({col_definitions})"
                
                logger.info("Executing: %s", create_table_sql)
                cursor.execute(create_table_sql)
                logger.info("Table %s created/replaced successfully.", full_table_name)
                actions.append(
                    "Created target table using inferred types and header-based column names."
                )
            else:
                logger.error("Could not infer schema from CSV file")
                raise Exception(f"Failed to infer schema from {stage_file_name}")

            copy_sql = (
                f"COPY INTO {full_table_name} "
                f"FROM @{stage_name}/{stage_file_name} "
                f"FILE_FORMAT = (FORMAT_NAME = '{settings.snowflake_file_format}') "
                "ON_ERROR = 'ABORT_STATEMENT'"
            )

            logger.info("Copying staged CSV into target table %s.%s", schema_name, target_table)
            cursor.execute(copy_sql)
            rows = cursor.fetchall()
            
            # COPY INTO returns: [FILE, STATUS, ROWS_PARSED, ROWS_LOADED, ERROR_LIMIT, ERRORS_SEEN, ...]
            # Extract ROWS_LOADED (index 3)
            if not rows:
                actions.append("Copied staged CSV into table, but no COPY INTO results were returned.")
                return 0, actions
            
            try:
                rows_loaded = int(rows[0][3]) if len(rows[0]) > 3 else 0
                logger.info("Successfully loaded %d rows", rows_loaded)
                actions.append(
                    f"Copied staged CSV into table {full_table_name}. Rows loaded: {rows_loaded}."
                )

                # Apply Snowpark transformations
                session = self.get_snowpark_session()
                df = session.table(target_table_name)  # Read the table we just created
                transformed_df, transform_actions = self.apply_snowpark_transformations(df)
                actions.extend(transform_actions)

                # Save the transformed data back to the table
                transformed_df.write.mode("overwrite").save_as_table(target_table_name)
                actions.append("Saved transformed DataFrame back to the target table.")

                return rows_loaded, actions
            except (ValueError, IndexError):
                logger.error("Could not parse COPY INTO response: %s", rows)
                actions.append("Copied staged CSV into table, but could not parse row count.")
                return 0, actions

    def apply_snowpark_transformations(self, df: DataFrame) -> tuple[DataFrame, list[str]]:
        """Apply Snowpark DataFrame transformations and return actions taken."""
        actions: list[str] = []
        logger.info("Applying Snowpark transformation logic to DataFrame")
        actions.append("Starting Snowpark DataFrame transformations.")

        # Trim whitespace for all string columns and standardize case.
        string_columns = [field.name for field in df.schema.fields if field.datatype.type_name.lower() == "string"]
        transformed = df
        if string_columns:
            actions.append(f"Trimming whitespace from string columns: {', '.join(string_columns)}")
            for column_name in string_columns:
                transformed = transformed.with_column(
                    column_name,
                    F.trim(F.col(column_name)).alias(column_name),
                )

        # Add a Snowflake-managed load timestamp.
        transformed = transformed.with_column("loaded_at", F.current_timestamp())
        actions.append("Added 'loaded_at' timestamp column with current timestamp.")

        # If any column looks like a date/timestamp, attempt a cast.
        date_columns = []
        for field in transformed.schema.fields:
            if "date" in field.name.lower() or "timestamp" in field.name.lower() or "ts" in field.name.lower():
                date_columns.append(field.name)

        if date_columns:
            actions.append(f"Converting date/timestamp columns to TIMESTAMP type: {', '.join(date_columns)}")
            for column_name in date_columns:
                transformed = transformed.with_column(
                    column_name,
                    F.to_timestamp(F.col(column_name)).alias(column_name),
                )

        actions.append("Snowpark DataFrame transformations completed.")
        return transformed, actions
        if not settings.snowflake_transform_procedure:
            return "No transform procedure configured."
        
        if settings.snowflake_transform_procedure.startswith("YOUR_"):
            message = (
                "Skipping transform procedure because configuration is still a placeholder."
            )
            logger.info(message)
            return message

        schema_name = schema_name or settings.snowflake_schema
        proc = settings.snowflake_transform_procedure
        qualified_table = f"{settings.snowflake_database}.{schema_name}.{target_table}"
        call_sql = f"CALL {proc}('{qualified_table}')"

        with self.connect().cursor() as cursor:
            logger.info("Calling Snowflake transform procedure: %s with table %s", proc, qualified_table)
            try:
                cursor.execute(call_sql)
                message = f"Transform procedure {proc} executed successfully."
                logger.info(message)
                return message
            except Exception as e:
                message = f"Transform procedure {proc} failed: {e}"
                logger.error(message)
                return message

    def _read_csv_header(self, csv_path: Path) -> list[str]:
        with csv_path.open(newline='', encoding='utf-8') as csv_file:
            reader = csv.reader(csv_file)
            for row in reader:
                if not row:
                    continue
                if row[0].startswith('\ufeff'):
                    row[0] = row[0].lstrip('\ufeff')
                header = [column.strip() for column in row if column.strip()]
                if header:
                    return header
        raise RuntimeError(f"CSV file {csv_path} does not contain a valid header row.")

    def get_infer_schema_sql(self, stage_file_name: str) -> str:
        """Generate SQL to view inferred schema from staged CSV file.
        
        Run this in Snowflake to create a table with auto-detected columns:
        CREATE TABLE ... AS SELECT * FROM TABLE(INFER_SCHEMA(...))
        """
        stage_name = quote_identifier(settings.snowflake_stage_name)
        return f"""
        SELECT *
        FROM TABLE(
            INFER_SCHEMA(
                LOCATION => '@{stage_name}/{stage_file_name}',
                FILE_FORMAT => '{settings.snowflake_file_format}'
            )
        )
        """
