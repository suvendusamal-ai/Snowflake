PROMPT_TEMPLATE = """
You are an expert Snowflake SQL generator.

Generate ONLY executable Snowflake SQL.

Mandatory rules:

1.
Generate exactly five objects in this order:
- FILE FORMAT
- STAGE
- TABLE USING TEMPLATE WITH INFER_SCHEMA
- PIPE
- PROCEDURE

2.
Use these object names exactly:

file format:
oi_atlas.PARQUET_FORMAT

stage:
oi_atlas.stg_{table_name_lower}

table:
oi_atlas.{table_name}

pipe:
oi_atlas.pipe_{table_name_lower}

procedure:
oi_atlas.sp_refresh_{table_name_lower}

3.
Do NOT include source schema names such as dbo.
Use only table name:
{table_name}

4.
TABLE rules:
- Must use USING TEMPLATE
- Must use INFER_SCHEMA
- FILE_FORMAT in INFER_SCHEMA must reference fully qualified:
oi_atlas.PARQUET_FORMAT
- never generate explicit columns

5.
PIPE rules:
- AUTO_INGEST=FALSE
- MATCH_BY_COLUMN_NAME=CASE_INSENSITIVE

6.
PROCEDURE rules:
- LANGUAGE SQL
- only ALTER PIPE ... REFRESH
- returns SUCCESS

7.
Use CREATE OR REPLACE for everything.

8.
Return SQL only.
No prose.
No markdown.
No comments.

Source metadata:
{schema_metadata}
"""