-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Internal Stages (per department)
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE SCHEMA RAW;

-- Department document stages
CREATE STAGE IF NOT EXISTS FINANCE_DOCS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Finance department document repository';

CREATE STAGE IF NOT EXISTS TREASURY_DOCS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Treasury department document repository';

CREATE STAGE IF NOT EXISTS PROCUREMENT_DOCS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Procurement department document repository';

CREATE STAGE IF NOT EXISTS RISK_DOCS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Risk department document repository';

CREATE STAGE IF NOT EXISTS COMPLIANCE_DOCS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Compliance department document repository';

CREATE STAGE IF NOT EXISTS AUDIT_DOCS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Audit department document repository';

CREATE STAGE IF NOT EXISTS HR_DOCS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Human Resources department document repository';

CREATE STAGE IF NOT EXISTS LEGAL_DOCS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Legal department document repository';

CREATE STAGE IF NOT EXISTS OPERATIONS_DOCS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Operations department document repository';

-- Shared processing stage for temporary files
CREATE STAGE IF NOT EXISTS PROCESSING_TEMP
    COMMENT = 'Temporary stage for in-flight document processing';
