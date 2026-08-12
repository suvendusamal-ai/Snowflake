-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Cortex Search Service: ENTERPRISE_KNOWLEDGE_SEARCH
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE WAREHOUSE CORTEX_AI_SEARCH_WH;

-- ============================================================================
-- Primary search service: Combines semantic (vector) + keyword (BM25) search.
-- Backed by DOCUMENT_CHUNKS table with embeddings.
--
-- Features:
-- - Hybrid search (vector + keyword for best recall)
-- - Filterable by DEPARTMENT, DOCUMENT_TYPE, SENSITIVITY_LEVEL
-- - Returns CHUNK_TEXT + metadata for grounding
-- ============================================================================
CREATE OR REPLACE CORTEX SEARCH SERVICE KNOWLEDGE.ENTERPRISE_KNOWLEDGE_SEARCH
    ON CHUNK_TEXT
    ATTRIBUTES DEPARTMENT, DOCUMENT_TYPE, SENSITIVITY_LEVEL, FILE_NAME, SECTION_HEADER
    WAREHOUSE = CORTEX_AI_SEARCH_WH
    TARGET_LAG = '5 minutes'
    EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
    COMMENT = 'Enterprise knowledge base search - hybrid semantic + keyword retrieval'
AS (
    SELECT
        CHUNK_ID,
        DOCUMENT_ID,
        CHUNK_TEXT,
        DEPARTMENT,
        DOCUMENT_TYPE,
        SENSITIVITY_LEVEL,
        FILE_NAME,
        SECTION_HEADER,
        CHUNK_INDEX
    FROM KNOWLEDGE.DOCUMENT_CHUNKS
    WHERE CHUNK_TEXT IS NOT NULL
        AND LENGTH(CHUNK_TEXT) > 50
);

-- ============================================================================
-- Per-department search services (optional, for strict isolation scenarios)
-- Uncomment if department-level search isolation is required beyond row access.
-- ============================================================================

-- CREATE OR REPLACE CORTEX SEARCH SERVICE KNOWLEDGE.FINANCE_SEARCH
--     ON CHUNK_TEXT
--     ATTRIBUTES DOCUMENT_TYPE, FILE_NAME, SECTION_HEADER
--     WAREHOUSE = CORTEX_AI_SEARCH_WH
--     TARGET_LAG = '10 minutes'
--     EMBEDDING_MODEL = 'snowflake-arctic-embed-l-v2.0'
-- AS (
--     SELECT CHUNK_ID, DOCUMENT_ID, CHUNK_TEXT, DOCUMENT_TYPE, FILE_NAME, SECTION_HEADER
--     FROM KNOWLEDGE.DOCUMENT_CHUNKS
--     WHERE DEPARTMENT = 'finance'
-- );
