-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Cortex Agent: ENTERPRISE_KNOWLEDGE_AGENT
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE SCHEMA AGENT;
USE WAREHOUSE CORTEX_AI_SEARCH_WH;

-- ============================================================================
-- Tool Functions: SQL functions that the agent can call
-- ============================================================================

-- Tool 1: Search the knowledge base
CREATE OR REPLACE FUNCTION AGENT.SEARCH_KNOWLEDGE(
    QUERY VARCHAR,
    DEPARTMENT VARCHAR DEFAULT NULL,
    MAX_RESULTS NUMBER DEFAULT 10
)
RETURNS TABLE (
    CHUNK_ID VARCHAR,
    DOCUMENT_ID VARCHAR,
    CHUNK_TEXT VARCHAR,
    FILE_NAME VARCHAR,
    DEPARTMENT VARCHAR,
    SECTION_HEADER VARCHAR,
    RELEVANCE_SCORE FLOAT
)
LANGUAGE SQL
AS $$
    SELECT
        CHUNK_ID,
        DOCUMENT_ID,
        CHUNK_TEXT,
        FILE_NAME,
        DEPARTMENT,
        SECTION_HEADER,
        VECTOR_COSINE_SIMILARITY(
            EMBEDDING,
            SNOWFLAKE.CORTEX.EMBED_TEXT_1024(
                'snowflake-arctic-embed-l-v2.0',
                QUERY
            )
        ) AS RELEVANCE_SCORE
    FROM KNOWLEDGE.DOCUMENT_CHUNKS
    WHERE EMBEDDING IS NOT NULL
        AND (DEPARTMENT = DEPARTMENT OR DEPARTMENT IS NULL)
    ORDER BY RELEVANCE_SCORE DESC
    LIMIT MAX_RESULTS
$$;

-- Tool 2: Get document catalog listing
CREATE OR REPLACE FUNCTION AGENT.GET_CATALOG(
    DEPT VARCHAR DEFAULT NULL,
    DOC_TYPE VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    DOCUMENT_ID VARCHAR,
    TITLE VARCHAR,
    DEPARTMENT VARCHAR,
    DOCUMENT_TYPE VARCHAR,
    SENSITIVITY_LEVEL VARCHAR,
    CHUNK_COUNT NUMBER,
    LAST_UPDATED VARCHAR
)
LANGUAGE SQL
AS $$
    SELECT
        DOCUMENT_ID,
        TITLE,
        DEPARTMENT,
        DOCUMENT_TYPE,
        SENSITIVITY_LEVEL,
        CHUNK_COUNT,
        TO_VARCHAR(LAST_UPDATED_AT, 'YYYY-MM-DD') AS LAST_UPDATED
    FROM KNOWLEDGE.KNOWLEDGE_CATALOG
    WHERE IS_ACTIVE = TRUE
        AND (DEPARTMENT = DEPT OR DEPT IS NULL)
        AND (DOCUMENT_TYPE = DOC_TYPE OR DOC_TYPE IS NULL)
    ORDER BY LAST_UPDATED_AT DESC
    LIMIT 20
$$;

-- Tool 3: Get document details
CREATE OR REPLACE FUNCTION AGENT.GET_DOCUMENT_DETAILS(DOC_ID VARCHAR)
RETURNS TABLE (
    DOCUMENT_ID VARCHAR,
    FILE_NAME VARCHAR,
    DEPARTMENT VARCHAR,
    DOCUMENT_TYPE VARCHAR,
    SENSITIVITY VARCHAR,
    WORD_COUNT NUMBER,
    SUMMARY VARCHAR,
    TOPICS ARRAY
)
LANGUAGE SQL
AS $$
    SELECT
        r.DOCUMENT_ID,
        r.FILE_NAME,
        cl.DEPARTMENT,
        cl.DOCUMENT_TYPE,
        cl.SENSITIVITY_LEVEL AS SENSITIVITY,
        p.WORD_COUNT,
        LEFT(p.PARSED_CONTENT, 2000) AS SUMMARY,
        cl.TOPICS
    FROM RAW.DOCUMENT_REGISTRY r
        LEFT JOIN PROCESSED.PARSED_DOCUMENTS p ON r.DOCUMENT_ID = p.DOCUMENT_ID
        LEFT JOIN PROCESSED.DOCUMENT_CLASSIFICATIONS cl ON r.DOCUMENT_ID = cl.DOCUMENT_ID
    WHERE r.DOCUMENT_ID = DOC_ID
$$;

-- Tool 4: Get document metadata
CREATE OR REPLACE FUNCTION AGENT.GET_DOCUMENT_METADATA(DOC_ID VARCHAR)
RETURNS TABLE (
    METADATA_KEY VARCHAR,
    METADATA_VALUE VARCHAR,
    CONFIDENCE FLOAT
)
LANGUAGE SQL
AS $$
    SELECT
        METADATA_KEY,
        METADATA_VALUE,
        CONFIDENCE
    FROM PROCESSED.DOCUMENT_METADATA
    WHERE DOCUMENT_ID = DOC_ID
    ORDER BY CONFIDENCE DESC
$$;

-- Tool 5: Department statistics
CREATE OR REPLACE FUNCTION AGENT.GET_DEPARTMENT_STATS(DEPT VARCHAR DEFAULT NULL)
RETURNS TABLE (
    DEPARTMENT VARCHAR,
    DOCUMENT_COUNT NUMBER,
    TOTAL_CHUNKS NUMBER,
    AVG_CHUNKS_PER_DOC FLOAT,
    LAST_DOCUMENT_DATE VARCHAR
)
LANGUAGE SQL
AS $$
    SELECT
        DEPARTMENT,
        COUNT(DISTINCT DOCUMENT_ID) AS DOCUMENT_COUNT,
        COUNT(*) AS TOTAL_CHUNKS,
        COUNT(*) / NULLIF(COUNT(DISTINCT DOCUMENT_ID), 0) AS AVG_CHUNKS_PER_DOC,
        TO_VARCHAR(MAX(CREATED_AT), 'YYYY-MM-DD') AS LAST_DOCUMENT_DATE
    FROM KNOWLEDGE.DOCUMENT_CHUNKS
    WHERE (DEPARTMENT = DEPT OR DEPT IS NULL)
    GROUP BY DEPARTMENT
    ORDER BY DOCUMENT_COUNT DESC
$$;

-- ============================================================================
-- CREATE AGENT: Enterprise Knowledge Agent
-- ============================================================================
CREATE OR REPLACE CORTEX AGENT AGENT.ENTERPRISE_KNOWLEDGE_AGENT
    MODEL = 'claude-3-5-sonnet'
    TOOLS = (
        AGENT.SEARCH_KNOWLEDGE,
        AGENT.GET_CATALOG,
        AGENT.GET_DOCUMENT_DETAILS,
        AGENT.GET_DOCUMENT_METADATA,
        AGENT.GET_DEPARTMENT_STATS,
        'KNOWLEDGE.ENTERPRISE_KNOWLEDGE_SEARCH'
    )
    SYSTEM_PROMPT = '
You are the Enterprise AI Knowledge Assistant. You help business users find
and understand information from internal enterprise documents.

RULES:
1. Only answer based on retrieved context. Never fabricate information.
2. Always cite your sources with document name and relevant section.
3. If you cannot find relevant information, say so clearly.
4. Respect department boundaries - only use documents the user has access to.
5. For numerical data, always reference the source document and date.
6. When multiple sources conflict, present both and note the discrepancy.
7. Use the search tool first, then get_document_details for more context if needed.
8. For broad questions, check the catalog first to understand available documents.

SEARCH STRATEGY:
- For specific questions: Use SEARCH_KNOWLEDGE with the user query
- For discovery questions: Use GET_CATALOG to show available documents
- For detail follow-ups: Use GET_DOCUMENT_DETAILS or GET_DOCUMENT_METADATA
- For overview requests: Use GET_DEPARTMENT_STATS

RESPONSE FORMAT:
- Keep answers concise and actionable
- Always include source citations: [Source: filename, section]
- If confidence is low, state uncertainty explicitly
'
    COMMENT = 'Enterprise Knowledge Assistant - searches across all department repositories';

-- ============================================================================
-- Populate Tool Registry (for programmatic access/UI display)
-- ============================================================================
INSERT INTO AGENT.TOOL_REGISTRY (TOOL_NAME, TOOL_TYPE, DESCRIPTION, SQL_FUNCTION_NAME, REQUIRES_DEPARTMENT)
VALUES
    ('search_knowledge', 'search', 'Search the enterprise knowledge base using natural language', 'AGENT.SEARCH_KNOWLEDGE', FALSE),
    ('get_catalog', 'catalog', 'Browse available documents in the knowledge catalog', 'AGENT.GET_CATALOG', FALSE),
    ('get_document_details', 'retrieval', 'Get detailed information about a specific document', 'AGENT.GET_DOCUMENT_DETAILS', FALSE),
    ('get_document_metadata', 'retrieval', 'Get extracted metadata for a specific document', 'AGENT.GET_DOCUMENT_METADATA', FALSE),
    ('get_department_stats', 'analytics', 'Get document statistics for a department', 'AGENT.GET_DEPARTMENT_STATS', FALSE);
