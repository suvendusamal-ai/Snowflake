import re
from app.core.config import settings
from app.api.services.snowflake_service import SnowflakeService


class CortexService:

    @staticmethod
    def _normalize_table_name(table_name):
        if "." in table_name:
            table_name = table_name.split(".")[-1]

        clean = re.sub(r"[^A-Za-z0-9_]", "_", table_name)
        return clean.upper(), clean.lower()


    @staticmethod
    def _build_prompt(table_name, metadata):

        cols = "\n".join(
            [f"- {c['column']} ({c['type']})" for c in metadata]
        )

        return f"""
Return ONLY Snowflake SQL.
No explanation.
No markdown.
No comments.
No text before SQL.
First line MUST start with:
CREATE OR REPLACE FILE FORMAT

Generate exactly these 5 objects only:

1. FILE FORMAT
2. INTERNAL STAGE
3. TABLE
4. PIPE
5. PROCEDURE

Rules:
- Internal stage only.
- Never reference AWS/S3/Azure/GCS.
- Do NOT use USING TEMPLATE.
- Use explicit columns from metadata.
- Procedure must be complete.

Columns:
{cols}

Required procedure:

CREATE OR REPLACE PROCEDURE oi_atlas.sp_refresh_{table_name.lower()}()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
ALTER PIPE oi_atlas.pipe_{table_name.lower()} REFRESH;
RETURN 'PIPE REFRESHED';
END;
$$;
"""


    @staticmethod
    def _fallback_sql(tu, tl, metadata):

        columns=[]

        for c in metadata:
            col = c["column"].upper()

            dtype=str(c["type"]).lower()

            if "int" in dtype:
                sf_type="NUMBER"

            elif "date" in dtype:
                sf_type="DATE"

            elif "time" in dtype:
                sf_type="TIMESTAMP"

            elif "decimal" in dtype or "numeric" in dtype:
                sf_type="NUMBER"

            else:
                sf_type="VARCHAR"

            columns.append(f"{col} {sf_type}")

        ddl=",\n".join(columns)


        return f"""
CREATE OR REPLACE FILE FORMAT oi_atlas.PARQUET_FORMAT
TYPE=PARQUET;

CREATE OR REPLACE STAGE oi_atlas.stg_{tl}
FILE_FORMAT=oi_atlas.PARQUET_FORMAT;

CREATE OR REPLACE TABLE oi_atlas.{tu}
(
{ddl}
);

CREATE OR REPLACE PIPE oi_atlas.pipe_{tl}
AUTO_INGEST=FALSE
AS
COPY INTO oi_atlas.{tu}
FROM @oi_atlas.stg_{tl}
FILE_FORMAT=(TYPE=PARQUET)
MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE;

CREATE OR REPLACE PROCEDURE oi_atlas.sp_refresh_{tl}()
RETURNS STRING
LANGUAGE SQL
AS
$$
BEGIN
ALTER PIPE oi_atlas.pipe_{tl} REFRESH;
RETURN 'PIPE REFRESHED';
END;
$$;
""".strip()



    @staticmethod
    def _strip_non_sql_text(sql):

        sql=sql.strip()

        # Remove markdown fences
        sql=sql.replace("```sql","").replace("```","")

        # Keep only from first CREATE onward
        m=re.search(
            r'CREATE\s+OR\s+REPLACE',
            sql,
            re.IGNORECASE
        )

        if m:
            sql=sql[m.start():]

        return sql.strip()



    @staticmethod
    def _repair_procedure(sql, tl):

        if f"sp_refresh_{tl}" not in sql:
            return sql

        if "RETURN 'PIPE REFRESHED';" not in sql:
            sql += "\nRETURN 'PIPE REFRESHED';"

        if "\nEND;" not in sql:
            sql += "\nEND;"

        if "$$;" not in sql:
            sql += "\n$$;"

        return sql



    @staticmethod
    def _validate_or_fix(sql, tu, tl, metadata):

        sql=CortexService._strip_non_sql_text(sql)

        u=sql.upper()

        forbidden=[
            "S3://",
            "EXTERNAL STAGE",
            "AZURE",
            "ADLS",
            "GCS"
        ]

        for bad in forbidden:
            if bad in u:
                return CortexService._fallback_sql(
                    tu,
                    tl,
                    metadata
                )


        required=[
            "CREATE OR REPLACE FILE FORMAT",
            "CREATE OR REPLACE STAGE",
            "CREATE OR REPLACE TABLE",
            "CREATE OR REPLACE PIPE",
            "CREATE OR REPLACE PROCEDURE"
        ]

        for req in required:
            if req not in u:
                return CortexService._fallback_sql(
                    tu,
                    tl,
                    metadata
                )


        sql=CortexService._repair_procedure(
            sql,
            tl
        )


        if "END;" not in sql or "$$;" not in sql:
            return CortexService._fallback_sql(
                tu,
                tl,
                metadata
            )

        return sql



    @staticmethod
    def generate(table_name, metadata):

        tu,tl=CortexService._normalize_table_name(
            table_name
        )

        prompt=CortexService._build_prompt(
            tu,
            metadata
        )

        conn=SnowflakeService.connection()
        cur=conn.cursor()

        try:

            stmt=f"""
SELECT SNOWFLAKE.CORTEX.COMPLETE(
'{settings.CORTEX_MODEL}',
$$
{prompt}
$$
)
"""

            cur.execute(stmt)

            result=cur.fetchone()[0]

            if isinstance(result,list):
                result="".join(result)


            return CortexService._validate_or_fix(
                result,
                tu,
                tl,
                metadata
            )

        except Exception as e:
            print("Cortex fallback triggered:",e)

            return CortexService._fallback_sql(
                tu,
                tl,
                metadata
            )

        finally:
            cur.close()
            conn.close()