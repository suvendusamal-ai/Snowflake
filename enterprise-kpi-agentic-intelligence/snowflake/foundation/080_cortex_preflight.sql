-- Diagnostic only. This script creates no objects and changes no account or user settings.
USE ROLE KPI_PLATFORM_ADMIN;
USE WAREHOUSE KPI_INTELLIGENCE_WH;

SELECT
    'SESSION_CONTEXT' AS check_name,
    IFF(CURRENT_ROLE() IS NOT NULL AND CURRENT_WAREHOUSE() IS NOT NULL, 'READY', 'ACTION REQUIRED') AS status,
    OBJECT_CONSTRUCT(
        'account', CURRENT_ACCOUNT(),
        'region', CURRENT_REGION(),
        'user', CURRENT_USER(),
        'role', CURRENT_ROLE(),
        'warehouse', CURRENT_WAREHOUSE()
    ) AS details;

SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;

SELECT
    'CROSS_REGION_POLICY' AS check_name,
    'MANUAL VERIFICATION REQUIRED' AS status,
    'Review the preceding account parameter against approved residency policy; do not change it in I3.' AS details;

SHOW DATABASE ROLES IN DATABASE SNOWFLAKE;

SELECT
    'CORTEX_DATABASE_ROLES' AS check_name,
    'MANUAL VERIFICATION REQUIRED' AS status,
    'Confirm documented Cortex roles and least-privilege grants for Analyst, Search, and Agents in this account.' AS details;

SHOW GRANTS TO ROLE KPI_AI_BUILDER;
SHOW GRANTS TO ROLE KPI_AI_RUNTIME;

SELECT
    'CORTEX_FEATURE_AVAILABILITY' AS check_name,
    'MANUAL VERIFICATION REQUIRED' AS status,
    'Verify region and account support for Cortex Analyst, Cortex Search, and Cortex Agents in Snowsight and current Snowflake documentation.' AS details
UNION ALL
SELECT
    'AI_RUNTIME_EXECUTION_MODEL',
    'MANUAL VERIFICATION REQUIRED',
    'Verify caller, owner, and runtime privilege behavior before granting feature-specific privileges.';
