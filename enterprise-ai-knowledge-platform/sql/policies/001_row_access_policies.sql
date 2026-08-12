-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Row Access Policies: Department-level document isolation
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE SCHEMA GOVERNANCE;

-- ============================================================================
-- Department mapping table: maps roles to departments they can access
-- ============================================================================
CREATE TABLE IF NOT EXISTS ROLE_DEPARTMENT_MAP (
    ROLE_NAME           VARCHAR(100) NOT NULL,
    DEPARTMENT          VARCHAR(50) NOT NULL,
    GRANTED_AT          TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP(),
    GRANTED_BY          VARCHAR(200),
    CONSTRAINT PK_ROLE_DEPT PRIMARY KEY (ROLE_NAME, DEPARTMENT)
)
COMMENT = 'Maps Snowflake roles to departments for row access policy enforcement';

-- Seed the role-department mappings
INSERT INTO ROLE_DEPARTMENT_MAP (ROLE_NAME, DEPARTMENT) VALUES
    ('CORTEX_AI_FINANCE', 'finance'),
    ('CORTEX_AI_TREASURY', 'treasury'),
    ('CORTEX_AI_PROCUREMENT', 'procurement'),
    ('CORTEX_AI_RISK', 'risk'),
    ('CORTEX_AI_COMPLIANCE', 'compliance'),
    ('CORTEX_AI_AUDIT', 'audit'),
    ('CORTEX_AI_HR', 'hr'),
    ('CORTEX_AI_LEGAL', 'legal'),
    ('CORTEX_AI_OPERATIONS', 'operations'),
    -- Admin and Service roles can access all departments
    ('CORTEX_AI_ADMIN', 'finance'),
    ('CORTEX_AI_ADMIN', 'treasury'),
    ('CORTEX_AI_ADMIN', 'procurement'),
    ('CORTEX_AI_ADMIN', 'risk'),
    ('CORTEX_AI_ADMIN', 'compliance'),
    ('CORTEX_AI_ADMIN', 'audit'),
    ('CORTEX_AI_ADMIN', 'hr'),
    ('CORTEX_AI_ADMIN', 'legal'),
    ('CORTEX_AI_ADMIN', 'operations'),
    ('CORTEX_AI_SERVICE', 'finance'),
    ('CORTEX_AI_SERVICE', 'treasury'),
    ('CORTEX_AI_SERVICE', 'procurement'),
    ('CORTEX_AI_SERVICE', 'risk'),
    ('CORTEX_AI_SERVICE', 'compliance'),
    ('CORTEX_AI_SERVICE', 'audit'),
    ('CORTEX_AI_SERVICE', 'hr'),
    ('CORTEX_AI_SERVICE', 'legal'),
    ('CORTEX_AI_SERVICE', 'operations');

-- ============================================================================
-- Row Access Policy: Restricts row visibility based on user's role → department
-- ============================================================================
CREATE OR REPLACE ROW ACCESS POLICY GOVERNANCE.DEPARTMENT_ROW_ACCESS
AS (department_col VARCHAR) RETURNS BOOLEAN ->
    -- Admin/Service bypass
    CURRENT_ROLE() IN ('CORTEX_AI_ADMIN', 'CORTEX_AI_SERVICE', 'SYSADMIN', 'ACCOUNTADMIN')
    OR
    -- Department role check via mapping table
    EXISTS (
        SELECT 1 FROM GOVERNANCE.ROLE_DEPARTMENT_MAP
        WHERE ROLE_NAME = CURRENT_ROLE()
          AND DEPARTMENT = department_col
    )
    OR
    -- Users inheriting department roles via CORTEX_AI_USER
    EXISTS (
        SELECT 1 FROM GOVERNANCE.ROLE_DEPARTMENT_MAP rdm
        WHERE rdm.DEPARTMENT = department_col
          AND IS_ROLE_IN_SESSION(rdm.ROLE_NAME)
    );

-- ============================================================================
-- Apply Row Access Policy to tables with DEPARTMENT column
-- ============================================================================

-- KNOWLEDGE.DOCUMENT_CHUNKS
ALTER TABLE KNOWLEDGE.DOCUMENT_CHUNKS
    ADD ROW ACCESS POLICY GOVERNANCE.DEPARTMENT_ROW_ACCESS
    ON (DEPARTMENT);

-- KNOWLEDGE.KNOWLEDGE_CATALOG
ALTER TABLE KNOWLEDGE.KNOWLEDGE_CATALOG
    ADD ROW ACCESS POLICY GOVERNANCE.DEPARTMENT_ROW_ACCESS
    ON (DEPARTMENT);

-- PROCESSED.DOCUMENT_CLASSIFICATIONS
ALTER TABLE PROCESSED.DOCUMENT_CLASSIFICATIONS
    ADD ROW ACCESS POLICY GOVERNANCE.DEPARTMENT_ROW_ACCESS
    ON (DEPARTMENT);

-- RAW.DOCUMENT_REGISTRY
ALTER TABLE RAW.DOCUMENT_REGISTRY
    ADD ROW ACCESS POLICY GOVERNANCE.DEPARTMENT_ROW_ACCESS
    ON (DEPARTMENT);
