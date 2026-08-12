-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Dynamic Tables: Automated chunk + embedding pipeline
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE WAREHOUSE CORTEX_AI_INGESTION_WH;

-- ============================================================================
-- Dynamic Table: DOCUMENT_CHUNKS_DT
-- Automatically generates chunks from PARSED_DOCUMENTS using the chunking UDF,
-- then produces embeddings via EMBED_TEXT.
--
-- Target lag: 5 minutes (balances freshness vs. compute cost)
-- ============================================================================
CREATE OR REPLACE DYNAMIC TABLE KNOWLEDGE.DOCUMENT_CHUNKS_DT
    TARGET_LAG = '5 minutes'
    WAREHOUSE = CORTEX_AI_INGESTION_WH
AS
SELECT
    UUID_STRING() AS CHUNK_ID,
    p.DOCUMENT_ID,
    c.INDEX AS CHUNK_INDEX,
    c.VALUE::VARCHAR AS CHUNK_TEXT,
    LENGTH(c.VALUE::VARCHAR) AS CHUNK_SIZE_CHARS,
    CAST(LENGTH(c.VALUE::VARCHAR) / 4 AS NUMBER) AS TOKEN_COUNT,
    cl.DEPARTMENT,
    cl.DOCUMENT_TYPE,
    cl.SENSITIVITY_LEVEL,
    r.FILE_NAME,
    SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
        'snowflake-arctic-embed-l-v2.0',
        LEFT(c.VALUE::VARCHAR, 8000)
    ) AS EMBEDDING,
    CURRENT_TIMESTAMP() AS CREATED_AT
FROM PROCESSED.PARSED_DOCUMENTS p
    INNER JOIN RAW.DOCUMENT_REGISTRY r
        ON p.DOCUMENT_ID = r.DOCUMENT_ID
    LEFT JOIN PROCESSED.DOCUMENT_CLASSIFICATIONS cl
        ON p.DOCUMENT_ID = cl.DOCUMENT_ID,
    LATERAL FLATTEN(
        INPUT => KNOWLEDGE.CHUNK_DOCUMENT_UDF(p.PARSED_CONTENT, 1500, 200)
    ) c
WHERE r.PROCESSING_STATUS = 'COMPLETED';

-- ============================================================================
-- Dynamic Table: KNOWLEDGE_CATALOG_DT
-- Aggregates chunk-level data into document-level catalog entries.
-- ============================================================================
CREATE OR REPLACE DYNAMIC TABLE KNOWLEDGE.KNOWLEDGE_CATALOG_DT
    TARGET_LAG = '10 minutes'
    WAREHOUSE = CORTEX_AI_INGESTION_WH
AS
SELECT
    UUID_STRING() AS CATALOG_ID,
    r.DOCUMENT_ID,
    r.FILE_NAME AS TITLE,
    LEFT(p.PARSED_CONTENT, 2000) AS SUMMARY,
    COALESCE(cl.DEPARTMENT, r.DEPARTMENT) AS DEPARTMENT,
    cl.DOCUMENT_TYPE,
    cl.SENSITIVITY_LEVEL,
    cl.TOPICS,
    COUNT(ch.CHUNK_ID) AS CHUNK_COUNT,
    SUM(ch.TOKEN_COUNT) AS TOTAL_TOKENS,
    r.FILE_NAME,
    r.FILE_TYPE,
    r.STAGE_PATH AS SOURCE_STAGE,
    MIN(ch.CREATED_AT) AS FIRST_INDEXED_AT,
    MAX(ch.CREATED_AT) AS LAST_UPDATED_AT,
    TRUE AS IS_ACTIVE
FROM RAW.DOCUMENT_REGISTRY r
    INNER JOIN PROCESSED.PARSED_DOCUMENTS p
        ON r.DOCUMENT_ID = p.DOCUMENT_ID
    LEFT JOIN PROCESSED.DOCUMENT_CLASSIFICATIONS cl
        ON r.DOCUMENT_ID = cl.DOCUMENT_ID
    LEFT JOIN KNOWLEDGE.DOCUMENT_CHUNKS ch
        ON r.DOCUMENT_ID = ch.DOCUMENT_ID
WHERE r.PROCESSING_STATUS = 'COMPLETED'
GROUP BY
    r.DOCUMENT_ID, r.FILE_NAME, p.PARSED_CONTENT,
    cl.DEPARTMENT, r.DEPARTMENT, cl.DOCUMENT_TYPE,
    cl.SENSITIVITY_LEVEL, cl.TOPICS, r.FILE_TYPE, r.STAGE_PATH;
