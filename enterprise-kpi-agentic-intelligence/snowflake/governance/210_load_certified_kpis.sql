-- Immutable fixture load: insert missing governance keys without overwriting existing content.
-- Conflicting rows remain unchanged and are reported by 290_verify_kpi_registry.sql.
USE ROLE KPI_PLATFORM_ADMIN;
USE WAREHOUSE KPI_INTELLIGENCE_WH;
USE DATABASE KPI_INTELLIGENCE_DB;
USE SCHEMA GOVERNANCE;

INSERT INTO KPI_REGISTRY (
    METRIC_ID, METRIC_VERSION, METRIC_NAME, BUSINESS_DEFINITION, DOMAIN,
    OWNER_ROLE, STEWARD_ROLE, CALCULATION_DESCRIPTION, TRUSTED_SOURCE_RELATION,
    METRIC_AMOUNT_COLUMN, METRIC_DATE_COLUMN, CERTIFICATION_STATUS,
    EFFECTIVE_FROM, EFFECTIVE_TO, APPROVAL_REFERENCE, BUSINESS_REASON,
    PREDECESSOR_METRIC_ID, PREDECESSOR_METRIC_VERSION, CREATED_AT, UPDATED_AT
)
SELECT
    source.METRIC_ID, source.METRIC_VERSION, source.METRIC_NAME,
    source.BUSINESS_DEFINITION, source.DOMAIN, source.OWNER_ROLE,
    source.STEWARD_ROLE, source.CALCULATION_DESCRIPTION,
    source.TRUSTED_SOURCE_RELATION, source.METRIC_AMOUNT_COLUMN,
    source.METRIC_DATE_COLUMN, source.CERTIFICATION_STATUS,
    source.EFFECTIVE_FROM, source.EFFECTIVE_TO, source.APPROVAL_REFERENCE,
    source.BUSINESS_REASON, source.PREDECESSOR_METRIC_ID,
    source.PREDECESSOR_METRIC_VERSION, source.CREATED_AT, source.UPDATED_AT
FROM VALUES
    (
        'SALES_BOOKINGS', 1, 'Sales Bookings',
        'Commercially accepted qualifying customer commitments, including signed booking, cancellation, and amendment events.',
        'SALES', 'Sales KPI Owner', 'Enterprise Data Steward',
        'Sum signed amount for immutable BOOKING, CANCELLATION, and AMENDMENT events using event_date for calendar-period attribution.',
        'KPI_INTELLIGENCE_DB.TRUSTED.FCT_SALES_BOOKINGS', 'AMOUNT', 'EVENT_DATE',
        'CERTIFIED', '2025-01-01'::DATE, NULL::DATE, 'I6-SALES-BOOKINGS-V1',
        'Establish an authoritative commercial-demand KPI distinct from Finance recognition.',
        NULL::VARCHAR, NULL::NUMBER(10, 0),
        '2025-07-01 00:00:00'::TIMESTAMP_NTZ, '2025-07-01 00:00:00'::TIMESTAMP_NTZ
    ),
    (
        'RECOGNIZED_REVENUE', 1, 'Recognized Revenue',
        'Value qualifying for recognition under approved management-reporting recognition conditions.',
        'FINANCE', 'Finance KPI Owner', 'Finance Controller',
        'Sum immutable recognition-event amount using recognition_date for calendar-period attribution; retain FULL, PARTIAL, FINAL, and ADJUSTMENT events.',
        'KPI_INTELLIGENCE_DB.TRUSTED.FCT_RECOGNIZED_REVENUE', 'AMOUNT', 'RECOGNITION_DATE',
        'CERTIFIED', '2025-01-01'::DATE, NULL::DATE, 'I6-RECOGNIZED-REVENUE-V1',
        'Establish an authoritative management-reporting recognition KPI distinct from commercial commitments.',
        NULL::VARCHAR, NULL::NUMBER(10, 0),
        '2025-07-01 00:00:00'::TIMESTAMP_NTZ, '2025-07-01 00:00:00'::TIMESTAMP_NTZ
    )
    AS source (
        METRIC_ID, METRIC_VERSION, METRIC_NAME, BUSINESS_DEFINITION, DOMAIN,
        OWNER_ROLE, STEWARD_ROLE, CALCULATION_DESCRIPTION, TRUSTED_SOURCE_RELATION,
        METRIC_AMOUNT_COLUMN, METRIC_DATE_COLUMN, CERTIFICATION_STATUS,
        EFFECTIVE_FROM, EFFECTIVE_TO, APPROVAL_REFERENCE, BUSINESS_REASON,
        PREDECESSOR_METRIC_ID, PREDECESSOR_METRIC_VERSION, CREATED_AT, UPDATED_AT
    )
WHERE NOT EXISTS (
    SELECT 1 FROM KPI_REGISTRY target
    WHERE target.METRIC_ID = source.METRIC_ID
      AND target.METRIC_VERSION = source.METRIC_VERSION
);

INSERT INTO KPI_SYNONYM (
    SYNONYM_ID, METRIC_ID, METRIC_VERSION, SYNONYM,
    NORMALIZED_SYNONYM, SYNONYM_TYPE, CREATED_AT
)
SELECT
    source.SYNONYM_ID, source.METRIC_ID, source.METRIC_VERSION, source.SYNONYM,
    source.NORMALIZED_SYNONYM, source.SYNONYM_TYPE, source.CREATED_AT
FROM VALUES
    ('SYN-SB-001', 'SALES_BOOKINGS', 1, 'sales bookings', 'sales bookings', 'CANONICAL_NAME', '2025-07-01 00:00:00'::TIMESTAMP_NTZ),
    ('SYN-SB-002', 'SALES_BOOKINGS', 1, 'bookings', 'bookings', 'APPROVED_ALIAS', '2025-07-01 00:00:00'::TIMESTAMP_NTZ),
    ('SYN-SB-003', 'SALES_BOOKINGS', 1, 'booked sales', 'booked sales', 'APPROVED_ALIAS', '2025-07-01 00:00:00'::TIMESTAMP_NTZ),
    ('SYN-SB-004', 'SALES_BOOKINGS', 1, 'commercial bookings', 'commercial bookings', 'APPROVED_ALIAS', '2025-07-01 00:00:00'::TIMESTAMP_NTZ),
    ('SYN-SB-005', 'SALES_BOOKINGS', 1, 'order bookings', 'order bookings', 'APPROVED_ALIAS', '2025-07-01 00:00:00'::TIMESTAMP_NTZ),
    ('SYN-SB-006', 'SALES_BOOKINGS', 1, 'booked business', 'booked business', 'APPROVED_ALIAS', '2025-07-01 00:00:00'::TIMESTAMP_NTZ),
    ('SYN-RR-001', 'RECOGNIZED_REVENUE', 1, 'recognized revenue', 'recognized revenue', 'CANONICAL_NAME', '2025-07-01 00:00:00'::TIMESTAMP_NTZ),
    ('SYN-RR-002', 'RECOGNIZED_REVENUE', 1, 'revenue', 'revenue', 'APPROVED_ALIAS', '2025-07-01 00:00:00'::TIMESTAMP_NTZ),
    ('SYN-RR-003', 'RECOGNIZED_REVENUE', 1, 'finance revenue', 'finance revenue', 'APPROVED_ALIAS', '2025-07-01 00:00:00'::TIMESTAMP_NTZ)
    AS source (
        SYNONYM_ID, METRIC_ID, METRIC_VERSION, SYNONYM,
        NORMALIZED_SYNONYM, SYNONYM_TYPE, CREATED_AT
    )
WHERE NOT EXISTS (
    SELECT 1 FROM KPI_SYNONYM target
    WHERE target.SYNONYM_ID = source.SYNONYM_ID
);

-- COMMONLY_CONFUSED_WITH is symmetric; REL-001 represents both directions.
-- This relationship supports explanation and discovery, never vocabulary matching.
INSERT INTO KPI_RELATIONSHIP (
    RELATIONSHIP_ID, SOURCE_METRIC_ID, TARGET_METRIC_ID,
    RELATIONSHIP_TYPE, RELATIONSHIP_REASON, CREATED_AT
)
SELECT
    source.RELATIONSHIP_ID, source.SOURCE_METRIC_ID, source.TARGET_METRIC_ID,
    source.RELATIONSHIP_TYPE, source.RELATIONSHIP_REASON, source.CREATED_AT
FROM VALUES
    (
        'REL-001', 'SALES_BOOKINGS', 'RECOGNIZED_REVENUE',
        'COMMONLY_CONFUSED_WITH',
        'Sales Bookings represents commercial commitment while Recognized Revenue represents Finance recognition. They are frequently compared or confused in enterprise reporting but are distinct certified KPI concepts.',
        '2025-07-01 00:00:00'::TIMESTAMP_NTZ
    )
    AS source (
        RELATIONSHIP_ID, SOURCE_METRIC_ID, TARGET_METRIC_ID,
        RELATIONSHIP_TYPE, RELATIONSHIP_REASON, CREATED_AT
    )
WHERE NOT EXISTS (
    SELECT 1 FROM KPI_RELATIONSHIP target
    WHERE target.RELATIONSHIP_ID = source.RELATIONSHIP_ID
);

INSERT INTO KPI_DECISION_PROVENANCE (
    PROVENANCE_ID, METRIC_ID, METRIC_VERSION, DECISION_TYPE,
    DECISION_SUMMARY, RATIONALE, APPROVED_BY, APPROVAL_REFERENCE,
    DECISION_DATE, EFFECTIVE_FROM, SUPERSEDES_PROVENANCE_ID, CREATED_AT
)
SELECT
    source.PROVENANCE_ID, source.METRIC_ID, source.METRIC_VERSION,
    source.DECISION_TYPE, source.DECISION_SUMMARY, source.RATIONALE,
    source.APPROVED_BY, source.APPROVAL_REFERENCE, source.DECISION_DATE,
    source.EFFECTIVE_FROM, source.SUPERSEDES_PROVENANCE_ID, source.CREATED_AT
FROM VALUES
    (
        'PROV-SB-001', 'SALES_BOOKINGS', 1, 'INITIAL_CERTIFICATION',
        'Certify immutable signed commercial events using event_date.',
        'Sales Bookings measures accepted commercial commitments. The commercial acceptance or effective event date determines the reporting period. Cancellations and amendments remain separate signed immutable events so history is not rewritten. Recognized Revenue is intentionally excluded because Finance recognition answers a different business question and may occur in another period.',
        'Enterprise KPI Governance Council', 'I6-SALES-BOOKINGS-V1',
        '2025-07-01'::DATE, '2025-01-01'::DATE, NULL::VARCHAR,
        '2025-07-01 00:00:00'::TIMESTAMP_NTZ
    ),
    (
        'PROV-RR-001', 'RECOGNIZED_REVENUE', 1, 'INITIAL_CERTIFICATION',
        'Certify immutable recognition events using recognition_date.',
        'Recognized Revenue measures value satisfying approved management-reporting recognition conditions. recognition_date determines the reporting period, which can differ from the commercial booking period. PARTIAL and FINAL events remain separate so staged recognition is preserved and auditable. Sales Bookings is intentionally excluded because a commercial commitment alone does not establish Finance recognition.',
        'Enterprise KPI Governance Council', 'I6-RECOGNIZED-REVENUE-V1',
        '2025-07-01'::DATE, '2025-01-01'::DATE, NULL::VARCHAR,
        '2025-07-01 00:00:00'::TIMESTAMP_NTZ
    )
    AS source (
        PROVENANCE_ID, METRIC_ID, METRIC_VERSION, DECISION_TYPE,
        DECISION_SUMMARY, RATIONALE, APPROVED_BY, APPROVAL_REFERENCE,
        DECISION_DATE, EFFECTIVE_FROM, SUPERSEDES_PROVENANCE_ID, CREATED_AT
    )
WHERE NOT EXISTS (
    SELECT 1 FROM KPI_DECISION_PROVENANCE target
    WHERE target.PROVENANCE_ID = source.PROVENANCE_ID
);
