-- ============================================================================
-- Enterprise AI Knowledge Platform
-- RAW Schema Tables
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE SCHEMA RAW;

-- Master document registry: every uploaded document is tracked here
CREATE TABLE IF NOT EXISTS DOCUMENT_REGISTRY (
    DOCUMENT_ID         VARCHAR(50) NOT NULL DEFAULT UUID_STRING(),
    FILE_NAME           VARCHAR(500) NOT NULL,
    FILE_TYPE           VARCHAR(20) NOT NULL,
    FILE_SIZE_BYTES     NUMBER(20) NOT NULL,
    DEPARTMENT          VARCHAR(50) NOT NULL,
    STAGE_PATH          VARCHAR(1000) NOT NULL,
    CHECKSUM_SHA256     VARCHAR(64),
    UPLOAD_TIMESTAMP    TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    UPLOADED_BY         VARCHAR(200),
    PROCESSING_STATUS   VARCHAR(20) DEFAULT 'PENDING',
    ERROR_MESSAGE       VARCHAR(5000),
    RETRY_COUNT         NUMBER(3) DEFAULT 0,
    LAST_PROCESSED_AT   TIMESTAMP_NTZ,
    CONSTRAINT PK_DOCUMENT_REGISTRY PRIMARY KEY (DOCUMENT_ID)
)
COMMENT = 'Master registry of all ingested documents'
CHANGE_TRACKING = TRUE;

-- Stream on DOCUMENT_REGISTRY for CDC-driven pipeline
CREATE STREAM IF NOT EXISTS DOCUMENT_REGISTRY_STREAM
    ON TABLE DOCUMENT_REGISTRY
    APPEND_ONLY = TRUE
    COMMENT = 'Captures new document registrations to trigger processing pipeline';
