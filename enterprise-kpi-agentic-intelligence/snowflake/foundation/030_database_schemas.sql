-- Bootstrap role: SYSADMIN. KPI_PLATFORM_ADMIN must already be granted to SYSADMIN.
USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS KPI_INTELLIGENCE_DB
    COMMENT = 'Enterprise KPI Trust and Agentic Intelligence Platform';

-- Remove the automatically created user schema; only approved project schemas remain.
DROP SCHEMA IF EXISTS KPI_INTELLIGENCE_DB.PUBLIC;

GRANT OWNERSHIP ON DATABASE KPI_INTELLIGENCE_DB
    TO ROLE KPI_PLATFORM_ADMIN;

USE ROLE KPI_PLATFORM_ADMIN;
USE DATABASE KPI_INTELLIGENCE_DB;

CREATE SCHEMA IF NOT EXISTS RAW WITH MANAGED ACCESS
    COMMENT = 'Immutable source-aligned data';
CREATE SCHEMA IF NOT EXISTS TRUSTED WITH MANAGED ACCESS
    COMMENT = 'Trusted Sales and Finance data products';
CREATE SCHEMA IF NOT EXISTS GOVERNANCE WITH MANAGED ACCESS
    COMMENT = 'KPI registry, certification, vocabulary, and decision provenance';
CREATE SCHEMA IF NOT EXISTS SEMANTIC WITH MANAGED ACCESS
    COMMENT = 'Bounded Sales and Finance semantic products';
CREATE SCHEMA IF NOT EXISTS AI WITH MANAGED ACCESS
    COMMENT = 'Governed AI capabilities';
CREATE SCHEMA IF NOT EXISTS AUDIT WITH MANAGED ACCESS
    COMMENT = 'Platform verification and audit records';
