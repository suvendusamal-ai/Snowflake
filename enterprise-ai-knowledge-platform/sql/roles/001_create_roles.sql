-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Role Hierarchy
-- ============================================================================

USE ROLE SECURITYADMIN;

-- Platform roles
CREATE ROLE IF NOT EXISTS CORTEX_AI_ADMIN
    COMMENT = 'Platform administrator - full access to all objects';
CREATE ROLE IF NOT EXISTS CORTEX_AI_SERVICE
    COMMENT = 'Service execution role - tasks, agents, UDFs';
CREATE ROLE IF NOT EXISTS CORTEX_AI_USER
    COMMENT = 'Read-only consumer role - business users via Streamlit';

-- Department roles
CREATE ROLE IF NOT EXISTS CORTEX_AI_FINANCE
    COMMENT = 'Finance department document access';
CREATE ROLE IF NOT EXISTS CORTEX_AI_TREASURY
    COMMENT = 'Treasury department document access';
CREATE ROLE IF NOT EXISTS CORTEX_AI_PROCUREMENT
    COMMENT = 'Procurement department document access';
CREATE ROLE IF NOT EXISTS CORTEX_AI_RISK
    COMMENT = 'Risk department document access';
CREATE ROLE IF NOT EXISTS CORTEX_AI_COMPLIANCE
    COMMENT = 'Compliance department document access';
CREATE ROLE IF NOT EXISTS CORTEX_AI_AUDIT
    COMMENT = 'Audit department document access';
CREATE ROLE IF NOT EXISTS CORTEX_AI_HR
    COMMENT = 'Human Resources department document access';
CREATE ROLE IF NOT EXISTS CORTEX_AI_LEGAL
    COMMENT = 'Legal department document access';
CREATE ROLE IF NOT EXISTS CORTEX_AI_OPERATIONS
    COMMENT = 'Operations department document access';

-- Role hierarchy: Department roles -> CORTEX_AI_USER -> CORTEX_AI_SERVICE -> CORTEX_AI_ADMIN -> SYSADMIN
GRANT ROLE CORTEX_AI_FINANCE TO ROLE CORTEX_AI_USER;
GRANT ROLE CORTEX_AI_TREASURY TO ROLE CORTEX_AI_USER;
GRANT ROLE CORTEX_AI_PROCUREMENT TO ROLE CORTEX_AI_USER;
GRANT ROLE CORTEX_AI_RISK TO ROLE CORTEX_AI_USER;
GRANT ROLE CORTEX_AI_COMPLIANCE TO ROLE CORTEX_AI_USER;
GRANT ROLE CORTEX_AI_AUDIT TO ROLE CORTEX_AI_USER;
GRANT ROLE CORTEX_AI_HR TO ROLE CORTEX_AI_USER;
GRANT ROLE CORTEX_AI_LEGAL TO ROLE CORTEX_AI_USER;
GRANT ROLE CORTEX_AI_OPERATIONS TO ROLE CORTEX_AI_USER;

GRANT ROLE CORTEX_AI_USER TO ROLE CORTEX_AI_SERVICE;
GRANT ROLE CORTEX_AI_SERVICE TO ROLE CORTEX_AI_ADMIN;
GRANT ROLE CORTEX_AI_ADMIN TO ROLE SYSADMIN;
