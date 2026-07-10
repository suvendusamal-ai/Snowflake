import pandas as pd
import os

from app.api.services.snowflake_service import SnowflakeService
from app.api.services.sqlserver_service import SQLServerService


class PipelineGenerator:

    # ---------------------------------------
    # GENERATE (UI DISPLAY ONLY)
    # ---------------------------------------
    @staticmethod
    def generate(source_type, database, table):

        table_clean = table.split('.')[-1].lower()
        schema = "oi_atlas"

        # Full SQL for UI (NOT fully executed)
        sql = f"""
CREATE OR REPLACE FILE FORMAT {schema}.parquet_format
TYPE=PARQUET;

CREATE OR REPLACE STAGE {schema}.stg_{table_clean}
FILE_FORMAT={schema}.parquet_format;

-- Table will be created dynamically AFTER file upload
CREATE OR REPLACE TABLE {schema}.{table_clean}
USING TEMPLATE (
  SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
  FROM TABLE(
    INFER_SCHEMA(
      LOCATION => '@{schema}.stg_{table_clean}',
      FILE_FORMAT => '{schema}.parquet_format'
    )
  )
);

CREATE OR REPLACE PIPE {schema}.pipe_{table_clean}
AUTO_INGEST=FALSE
AS
COPY INTO {schema}.{table_clean}
FROM @{schema}.stg_{table_clean}
FILE_FORMAT=(TYPE=PARQUET)
MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;

CREATE OR REPLACE PROCEDURE {schema}.sp_refresh_{table_clean}()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
  ALTER PIPE {schema}.pipe_{table_clean} REFRESH;
  RETURN 'PIPE REFRESHED';
END;
$$;
"""
        return sql.strip()

    # ---------------------------------------
    # DEPLOY (FINAL STABLE VERSION)
    # ---------------------------------------
    @staticmethod
    def deploy(generated_sql, source_table, database):

        table_clean = source_table.split('.')[-1].lower()
        schema = "oi_atlas"

        print(f"\n🚀 Deploying for table: {source_table} (DB: {database})")

        # -----------------------------------
        # STEP 1: READ FROM SQL SERVER
        # -----------------------------------
        conn_sql = SQLServerService.get_connection()
        cursor = conn_sql.cursor()
        cursor.execute(f"USE {database}")

        print(f"Reading from SQL Server: {source_table}")
        df = pd.read_sql(f"SELECT * FROM {source_table}", conn_sql)

        if df.empty:
            raise Exception("❌ Source table is empty")

        # -----------------------------------
        # STEP 2: WRITE PARQUET
        # -----------------------------------
        file_name = f"{table_clean}.parquet"
        df.to_parquet(file_name, index=False)

        print(f"✅ Parquet created: {file_name}")

        # -----------------------------------
        # STEP 3: EXECUTE ONLY SAFE SQL
        # (FILE FORMAT + STAGE ONLY)
        # -----------------------------------
        statements = generated_sql.split(";")

        for stmt in statements:
            stmt_clean = stmt.strip().upper()

            if not stmt_clean:
                continue

            # ❌ Skip unsafe statements
            if (
                "CREATE OR REPLACE TABLE" in stmt_clean
                or "CREATE OR REPLACE PIPE" in stmt_clean
                or "CREATE OR REPLACE PROCEDURE" in stmt_clean
                or "RETURN" in stmt_clean
                or "BEGIN" in stmt_clean
                or "END" in stmt_clean
                or "$$" in stmt_clean
            ):
                continue

            print("\nExecuting:\n", stmt)
            SnowflakeService.execute(stmt)

        # -----------------------------------
        # STEP 4: UPLOAD FILE FIRST (CRITICAL)
        # -----------------------------------
        put_sql = f"""
PUT file://{os.path.abspath(file_name)}
@{schema}.stg_{table_clean}
AUTO_COMPRESS=FALSE
OVERWRITE=TRUE;
"""
        print("\nUploading file...")
        SnowflakeService.execute(put_sql)
        print("✅ Upload complete")

        # -----------------------------------
        # STEP 5: CREATE TABLE (SAFE NOW)
        # -----------------------------------
        create_table_sql = f"""
CREATE OR REPLACE TABLE {schema}.{table_clean}
USING TEMPLATE (
  SELECT ARRAY_AGG(OBJECT_CONSTRUCT(*))
  FROM TABLE(
    INFER_SCHEMA(
      LOCATION => '@{schema}.stg_{table_clean}',
      FILE_FORMAT => '{schema}.parquet_format'
    )
  )
);
"""
        print("\nCreating table...")
        SnowflakeService.execute(create_table_sql)
        print("✅ Table created")

        # -----------------------------------
        # STEP 6: LOAD DATA
        # -----------------------------------
        copy_sql = f"""
COPY INTO {schema}.{table_clean}
FROM @{schema}.stg_{table_clean}
FILE_FORMAT=(TYPE=PARQUET)
MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;
"""
        print("\nLoading data...")
        SnowflakeService.execute(copy_sql)
        print("✅ DATA LOADED")

        # -----------------------------------
        # STEP 7: PREVIEW (TOP 10)
        # -----------------------------------
        preview = SnowflakeService.fetch_all(
            f"SELECT * FROM {schema}.{table_clean} LIMIT 10"
        )

        return {
            "status": "success",
            "table": table_clean,
            "preview": preview
        }