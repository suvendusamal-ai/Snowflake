-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Object Tags: Classification and governance metadata
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE SCHEMA GOVERNANCE;

-- ============================================================================
-- Tag Definitions
-- ============================================================================

-- Department tag
CREATE OR REPLACE TAG GOVERNANCE.DEPARTMENT
    ALLOWED_VALUES = 'finance', 'treasury', 'procurement', 'risk',
                     'compliance', 'audit', 'hr', 'legal', 'operations'
    COMMENT = 'Business department that owns the data';

-- Sensitivity classification tag
CREATE OR REPLACE TAG GOVERNANCE.SENSITIVITY_LEVEL
    ALLOWED_VALUES = 'public', 'internal', 'confidential', 'restricted'
    COMMENT = 'Data sensitivity classification';

-- Data domain tag
CREATE OR REPLACE TAG GOVERNANCE.DATA_DOMAIN
    ALLOWED_VALUES = 'document', 'knowledge', 'agent', 'governance', 'observability'
    COMMENT = 'Logical data domain';

-- PII indicator tag
CREATE OR REPLACE TAG GOVERNANCE.CONTAINS_PII
    ALLOWED_VALUES = 'true', 'false'
    COMMENT = 'Indicates whether the object may contain PII';

-- Retention policy tag
CREATE OR REPLACE TAG GOVERNANCE.RETENTION_DAYS
    COMMENT = 'Data retention period in days';

-- ============================================================================
-- Apply Tags to Schemas
-- ============================================================================
ALTER SCHEMA RAW SET TAG
    GOVERNANCE.DATA_DOMAIN = 'document',
    GOVERNANCE.SENSITIVITY_LEVEL = 'internal';

ALTER SCHEMA PROCESSED SET TAG
    GOVERNANCE.DATA_DOMAIN = 'document',
    GOVERNANCE.SENSITIVITY_LEVEL = 'confidential';

ALTER SCHEMA KNOWLEDGE SET TAG
    GOVERNANCE.DATA_DOMAIN = 'knowledge',
    GOVERNANCE.SENSITIVITY_LEVEL = 'internal';

ALTER SCHEMA AGENT SET TAG
    GOVERNANCE.DATA_DOMAIN = 'agent',
    GOVERNANCE.SENSITIVITY_LEVEL = 'confidential';

ALTER SCHEMA GOVERNANCE SET TAG
    GOVERNANCE.DATA_DOMAIN = 'governance',
    GOVERNANCE.SENSITIVITY_LEVEL = 'restricted';

ALTER SCHEMA OBSERVABILITY SET TAG
    GOVERNANCE.DATA_DOMAIN = 'observability',
    GOVERNANCE.SENSITIVITY_LEVEL = 'internal';

-- ============================================================================
-- Apply Tags to Critical Tables
-- ============================================================================
ALTER TABLE PROCESSED.DOCUMENT_METADATA SET TAG
    GOVERNANCE.CONTAINS_PII = 'true',
    GOVERNANCE.RETENTION_DAYS = '365';

ALTER TABLE AGENT.CONVERSATION_MESSAGES SET TAG
    GOVERNANCE.CONTAINS_PII = 'true',
    GOVERNANCE.RETENTION_DAYS = '180';

ALTER TABLE AGENT.CONVERSATIONS SET TAG
    GOVERNANCE.CONTAINS_PII = 'false',
    GOVERNANCE.RETENTION_DAYS = '365';

ALTER TABLE KNOWLEDGE.DOCUMENT_CHUNKS SET TAG
    GOVERNANCE.CONTAINS_PII = 'false',
    GOVERNANCE.RETENTION_DAYS = '730';
