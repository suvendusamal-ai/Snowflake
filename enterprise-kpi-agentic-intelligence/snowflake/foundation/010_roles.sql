-- Bootstrap role: SECURITYADMIN
USE ROLE SECURITYADMIN;

CREATE ROLE IF NOT EXISTS KPI_PLATFORM_ADMIN
    COMMENT = 'Owns and administers the Enterprise KPI platform foundation';
CREATE ROLE IF NOT EXISTS KPI_DATA_ENGINEER
    COMMENT = 'Builds RAW and TRUSTED data products';
CREATE ROLE IF NOT EXISTS KPI_SEMANTIC_ENGINEER
    COMMENT = 'Builds governed semantic products from trusted data';
CREATE ROLE IF NOT EXISTS KPI_AI_BUILDER
    COMMENT = 'Builds governed AI capabilities in the AI boundary';
CREATE ROLE IF NOT EXISTS KPI_AI_RUNTIME
    COMMENT = 'Runs approved Enterprise KPI Agent capabilities without build privileges';
CREATE ROLE IF NOT EXISTS KPI_EXECUTIVE
    COMMENT = 'Consumes governed KPI answers through the Enterprise KPI Agent';
CREATE ROLE IF NOT EXISTS KPI_AUDITOR
    COMMENT = 'Reads KPI governance and audit evidence';

-- Functional roles are siblings. None inherits another functional role.
GRANT ROLE KPI_DATA_ENGINEER TO ROLE KPI_PLATFORM_ADMIN;
GRANT ROLE KPI_SEMANTIC_ENGINEER TO ROLE KPI_PLATFORM_ADMIN;
GRANT ROLE KPI_AI_BUILDER TO ROLE KPI_PLATFORM_ADMIN;
GRANT ROLE KPI_AI_RUNTIME TO ROLE KPI_PLATFORM_ADMIN;
GRANT ROLE KPI_EXECUTIVE TO ROLE KPI_PLATFORM_ADMIN;
GRANT ROLE KPI_AUDITOR TO ROLE KPI_PLATFORM_ADMIN;

-- Administrative oversight remains in the standard system hierarchy.
GRANT ROLE KPI_PLATFORM_ADMIN TO ROLE SYSADMIN;
