-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Masking Policies: PII protection in extracted content
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE SCHEMA GOVERNANCE;

-- ============================================================================
-- Masking Policy: Full mask for confidential text fields
-- Returns '****' for non-privileged roles
-- ============================================================================
CREATE OR REPLACE MASKING POLICY GOVERNANCE.PII_TEXT_MASK
AS (val VARCHAR) RETURNS VARCHAR ->
    CASE
        WHEN CURRENT_ROLE() IN ('CORTEX_AI_ADMIN', 'SYSADMIN', 'ACCOUNTADMIN')
            THEN val
        WHEN IS_ROLE_IN_SESSION('CORTEX_AI_SERVICE')
            THEN val
        ELSE '****MASKED****'
    END;

-- ============================================================================
-- Masking Policy: Partial mask for email addresses
-- Shows domain but masks local part: j***@company.com
-- ============================================================================
CREATE OR REPLACE MASKING POLICY GOVERNANCE.EMAIL_MASK
AS (val VARCHAR) RETURNS VARCHAR ->
    CASE
        WHEN CURRENT_ROLE() IN ('CORTEX_AI_ADMIN', 'SYSADMIN', 'ACCOUNTADMIN')
            THEN val
        WHEN IS_ROLE_IN_SESSION('CORTEX_AI_SERVICE')
            THEN val
        WHEN val IS NULL THEN NULL
        ELSE
            LEFT(val, 1) || '***@' || SPLIT_PART(val, '@', 2)
    END;

-- ============================================================================
-- Masking Policy: Full redaction for sensitive metadata values
-- (SSN, credit card, etc.)
-- ============================================================================
CREATE OR REPLACE MASKING POLICY GOVERNANCE.SENSITIVE_VALUE_MASK
AS (val VARCHAR) RETURNS VARCHAR ->
    CASE
        WHEN CURRENT_ROLE() IN ('CORTEX_AI_ADMIN', 'SYSADMIN', 'ACCOUNTADMIN')
            THEN val
        WHEN IS_ROLE_IN_SESSION('CORTEX_AI_SERVICE')
            THEN val
        -- Mask SSN pattern: show last 4 only
        WHEN REGEXP_LIKE(val, '\\d{3}-\\d{2}-\\d{4}')
            THEN '***-**-' || RIGHT(val, 4)
        -- Mask credit card: show last 4 only
        WHEN REGEXP_LIKE(val, '\\d{4}[- ]?\\d{4}[- ]?\\d{4}[- ]?\\d{4}')
            THEN '****-****-****-' || RIGHT(REGEXP_REPLACE(val, '[^0-9]', ''), 4)
        ELSE '****REDACTED****'
    END;

-- ============================================================================
-- Apply masking policies to sensitive columns
-- ============================================================================

-- Metadata values may contain PII extracted from documents
ALTER TABLE PROCESSED.DOCUMENT_METADATA
    MODIFY COLUMN METADATA_VALUE
    SET MASKING POLICY GOVERNANCE.SENSITIVE_VALUE_MASK;

-- Conversation content may contain PII shared by users
-- (Apply selectively based on compliance requirements)
-- ALTER TABLE AGENT.CONVERSATION_MESSAGES
--     MODIFY COLUMN CONTENT
--     SET MASKING POLICY GOVERNANCE.PII_TEXT_MASK;
