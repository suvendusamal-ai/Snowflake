-- ============================================================================
-- Enterprise AI Knowledge Platform
-- GOVERNANCE Schema Tables
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE SCHEMA GOVERNANCE;

-- Access audit log: tracks who accessed what
CREATE TABLE IF NOT EXISTS ACCESS_AUDIT_LOG (
    AUDIT_ID            VARCHAR(50) NOT NULL DEFAULT UUID_STRING(),
    EVENT_TYPE          VARCHAR(50) NOT NULL,
    USER_ID             VARCHAR(200),
    USER_ROLE           VARCHAR(100),
    RESOURCE_TYPE       VARCHAR(50),
    RESOURCE_ID         VARCHAR(200),
    DEPARTMENT          VARCHAR(50),
    ACTION              VARCHAR(50),
    OUTCOME             VARCHAR(20),
    DETAILS             VARIANT,
    IP_ADDRESS          VARCHAR(50),
    SESSION_ID          VARCHAR(200),
    CREATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT PK_ACCESS_AUDIT PRIMARY KEY (AUDIT_ID)
)
COMMENT = 'Comprehensive access audit log for governance and compliance';

-- AI governance log: tracks AI decisions, guardrail violations, model usage
CREATE TABLE IF NOT EXISTS AI_GOVERNANCE_LOG (
    LOG_ID              VARCHAR(50) NOT NULL DEFAULT UUID_STRING(),
    EVENT_TYPE          VARCHAR(50) NOT NULL,
    CONVERSATION_ID     VARCHAR(50),
    USER_ID             VARCHAR(200),
    MODEL               VARCHAR(100),
    INPUT_TOKENS        NUMBER(10),
    OUTPUT_TOKENS       NUMBER(10),
    GUARDRAIL_RESULTS   VARIANT,
    VIOLATION_TYPE      VARCHAR(100),
    VIOLATION_DETAILS   VARCHAR(5000),
    ACTION_TAKEN        VARCHAR(50),
    CREATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT PK_AI_GOVERNANCE PRIMARY KEY (LOG_ID)
)
COMMENT = 'AI-specific governance events: model usage, guardrail outcomes, violations';

-- Data lineage tracking
CREATE TABLE IF NOT EXISTS DATA_LINEAGE (
    LINEAGE_ID          VARCHAR(50) NOT NULL DEFAULT UUID_STRING(),
    SOURCE_OBJECT       VARCHAR(500) NOT NULL,
    TARGET_OBJECT       VARCHAR(500) NOT NULL,
    TRANSFORMATION_TYPE VARCHAR(100),
    DESCRIPTION         VARCHAR(2000),
    CREATED_BY          VARCHAR(200),
    CREATED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    CONSTRAINT PK_DATA_LINEAGE PRIMARY KEY (LINEAGE_ID)
)
COMMENT = 'Manual data lineage tracking for document → chunk → response flow';

-- Seed lineage for the platform pipeline
INSERT INTO DATA_LINEAGE (SOURCE_OBJECT, TARGET_OBJECT, TRANSFORMATION_TYPE, DESCRIPTION) VALUES
    ('RAW.DOCUMENT_REGISTRY', 'PROCESSED.PARSED_DOCUMENTS', 'AI_PARSE_DOCUMENT', 'Document parsing and text extraction'),
    ('PROCESSED.PARSED_DOCUMENTS', 'PROCESSED.DOCUMENT_CLASSIFICATIONS', 'CORTEX_COMPLETE', 'AI-driven document classification'),
    ('PROCESSED.PARSED_DOCUMENTS', 'PROCESSED.DOCUMENT_METADATA', 'CORTEX_COMPLETE', 'AI metadata extraction'),
    ('PROCESSED.PARSED_DOCUMENTS', 'KNOWLEDGE.DOCUMENT_CHUNKS', 'CHUNK_DOCUMENT_UDF', 'Semantic text chunking'),
    ('KNOWLEDGE.DOCUMENT_CHUNKS', 'KNOWLEDGE.DOCUMENT_CHUNKS.EMBEDDING', 'EMBED_TEXT_1024', 'Vector embedding generation'),
    ('KNOWLEDGE.DOCUMENT_CHUNKS', 'KNOWLEDGE.ENTERPRISE_KNOWLEDGE_SEARCH', 'CORTEX_SEARCH', 'Search index population'),
    ('KNOWLEDGE.DOCUMENT_CHUNKS', 'KNOWLEDGE.KNOWLEDGE_CATALOG', 'AGGREGATION', 'Document-level catalog aggregation');
