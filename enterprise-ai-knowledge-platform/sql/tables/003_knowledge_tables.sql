-- ============================================================================
-- Enterprise AI Knowledge Platform
-- KNOWLEDGE Schema Tables
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE SCHEMA KNOWLEDGE;

-- Document chunks with embeddings
CREATE TABLE IF NOT EXISTS DOCUMENT_CHUNKS (
    CHUNK_ID            VARCHAR(50) NOT NULL DEFAULT UUID_STRING(),
    DOCUMENT_ID         VARCHAR(50) NOT NULL,
    CHUNK_INDEX         NUMBER(5) NOT NULL,
    CHUNK_TEXT          VARCHAR(16777216) NOT NULL,
    CHUNK_SIZE_CHARS    NUMBER(10),
    TOKEN_COUNT         NUMBER(10),
    SECTION_HEADER      VARCHAR(500),
    PAGE_NUMBER         NUMBER(5),
    DEPARTMENT          VARCHAR(50) NOT NULL,
    DOCUMENT_TYPE       VARCHAR(50),
    SENSITIVITY_LEVEL   VARCHAR(20) DEFAULT 'INTERNAL',
    FILE_NAME           VARCHAR(500),
    EMBEDDING           VECTOR(FLOAT, 1024),
    CREATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT PK_DOCUMENT_CHUNKS PRIMARY KEY (CHUNK_ID)
)
COMMENT = 'Document chunks with vector embeddings for semantic search';

-- Knowledge catalog: high-level document summaries for discovery
CREATE TABLE IF NOT EXISTS KNOWLEDGE_CATALOG (
    CATALOG_ID          VARCHAR(50) NOT NULL DEFAULT UUID_STRING(),
    DOCUMENT_ID         VARCHAR(50) NOT NULL,
    TITLE               VARCHAR(1000),
    SUMMARY             VARCHAR(5000),
    DEPARTMENT          VARCHAR(50) NOT NULL,
    DOCUMENT_TYPE       VARCHAR(50),
    SENSITIVITY_LEVEL   VARCHAR(20) DEFAULT 'INTERNAL',
    TOPICS              ARRAY,
    KEY_ENTITIES        ARRAY,
    CHUNK_COUNT         NUMBER(5),
    TOTAL_TOKENS        NUMBER(10),
    FILE_NAME           VARCHAR(500),
    FILE_TYPE           VARCHAR(20),
    SOURCE_STAGE        VARCHAR(200),
    FIRST_INDEXED_AT    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    LAST_UPDATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    IS_ACTIVE           BOOLEAN DEFAULT TRUE,
    CONSTRAINT PK_KNOWLEDGE_CATALOG PRIMARY KEY (CATALOG_ID)
)
COMMENT = 'Knowledge catalog - document-level summaries for discovery and navigation';

-- Chunk lineage: tracks which parsed content produced which chunks
CREATE TABLE IF NOT EXISTS CHUNK_LINEAGE (
    LINEAGE_ID          VARCHAR(50) NOT NULL DEFAULT UUID_STRING(),
    CHUNK_ID            VARCHAR(50) NOT NULL,
    DOCUMENT_ID         VARCHAR(50) NOT NULL,
    SOURCE_PARSE_ID     VARCHAR(50),
    CHUNKING_STRATEGY   VARCHAR(50),
    CHUNK_CONFIG        VARIANT,
    CREATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT PK_CHUNK_LINEAGE PRIMARY KEY (LINEAGE_ID)
)
COMMENT = 'Lineage tracking: parsed content -> chunks mapping';

-- Search feedback: captures user feedback on search quality
CREATE TABLE IF NOT EXISTS SEARCH_FEEDBACK (
    FEEDBACK_ID         VARCHAR(50) NOT NULL DEFAULT UUID_STRING(),
    QUERY_TEXT          VARCHAR(5000),
    CHUNK_ID            VARCHAR(50),
    RELEVANCE_SCORE     NUMBER(2),
    USER_FEEDBACK       VARCHAR(20),
    USER_ROLE           VARCHAR(100),
    CREATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT PK_SEARCH_FEEDBACK PRIMARY KEY (FEEDBACK_ID)
)
COMMENT = 'User feedback on search result relevance for continuous improvement';
