-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Database Creation
-- ============================================================================

USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS CORTEX_AI_PLATFORM
    DATA_RETENTION_TIME_IN_DAYS = 14
    COMMENT = 'Enterprise AI Knowledge Platform - Cortex AI powered knowledge management';

USE DATABASE CORTEX_AI_PLATFORM;
