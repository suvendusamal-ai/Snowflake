-- Read-only verification of the governed KPI registry and deterministic vocabulary contract.
USE ROLE KPI_PLATFORM_ADMIN;
USE WAREHOUSE KPI_INTELLIGENCE_WH;
USE DATABASE KPI_INTELLIGENCE_DB;
USE SCHEMA GOVERNANCE;

WITH candidate_terms AS (
    SELECT column1::VARCHAR AS NORMALIZED_TERM
    FROM VALUES
        ('sales bookings'), ('bookings'), ('recognized revenue'), ('revenue'),
        ('unknown term'), ('relationship-only term'), ('how did we perform')
),
effective_certified_registry AS (
    SELECT *
    FROM KPI_REGISTRY
    WHERE CERTIFICATION_STATUS = 'CERTIFIED'
      AND '2025-07-01'::DATE >= EFFECTIVE_FROM
      AND (EFFECTIVE_TO IS NULL OR '2025-07-01'::DATE <= EFFECTIVE_TO)
),
-- Candidate matching uses only canonical registry names and approved synonyms.
-- KPI_RELATIONSHIP is intentionally absent and cannot create or rank candidates.
candidate_matches AS (
    SELECT terms.NORMALIZED_TERM, registry.METRIC_ID, registry.METRIC_VERSION
    FROM candidate_terms terms
    JOIN effective_certified_registry registry
      ON LOWER(TRIM(registry.METRIC_NAME)) = terms.NORMALIZED_TERM
    UNION
    SELECT terms.NORMALIZED_TERM, registry.METRIC_ID, registry.METRIC_VERSION
    FROM candidate_terms terms
    JOIN KPI_SYNONYM synonym
      ON synonym.NORMALIZED_SYNONYM = terms.NORMALIZED_TERM
    JOIN effective_certified_registry registry
      ON registry.METRIC_ID = synonym.METRIC_ID
     AND registry.METRIC_VERSION = synonym.METRIC_VERSION
),
status_negative_controls AS (
    SELECT column1::VARCHAR AS METRIC_ID, column2::NUMBER(10, 0) AS METRIC_VERSION,
           column3::VARCHAR AS METRIC_NAME, column4::VARCHAR AS CERTIFICATION_STATUS,
           column5::DATE AS EFFECTIVE_FROM, column6::DATE AS EFFECTIVE_TO
    FROM VALUES
        ('CONTROL_DRAFT', 1, 'bookings', 'DRAFT',
         '2025-01-01'::DATE, NULL::DATE),
        ('CONTROL_DEPRECATED', 1, 'revenue', 'DEPRECATED',
         '2025-01-01'::DATE, NULL::DATE)
),
eligible_status_negative_controls AS (
    SELECT *
    FROM status_negative_controls
    WHERE CERTIFICATION_STATUS = 'CERTIFIED'
      AND '2025-07-01'::DATE >= EFFECTIVE_FROM
      AND (EFFECTIVE_TO IS NULL OR '2025-07-01'::DATE <= EFFECTIVE_TO)
),
expected_synonyms AS (
    SELECT column1::VARCHAR AS SYNONYM_ID, column2::VARCHAR AS METRIC_ID,
           column3::NUMBER(10, 0) AS METRIC_VERSION, column4::VARCHAR AS SYNONYM,
           column5::VARCHAR AS NORMALIZED_SYNONYM, column6::VARCHAR AS SYNONYM_TYPE,
           column7::TIMESTAMP_NTZ AS CREATED_AT
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
),
verification AS (
    SELECT 1 AS CHECK_ID, 'EXPECTED_GOVERNANCE_TABLES' AS CHECK_NAME,
           IFF((SELECT COUNT(*) FROM KPI_INTELLIGENCE_DB.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'GOVERNANCE' AND TABLE_TYPE = 'BASE TABLE'
                  AND TABLE_NAME IN ('KPI_REGISTRY', 'KPI_SYNONYM', 'KPI_RELATIONSHIP',
                                     'KPI_DECISION_PROVENANCE')) = 4,
               'PASS', 'FAIL') AS STATUS,
           OBJECT_CONSTRUCT('expected', 4, 'actual',
               (SELECT COUNT(*) FROM KPI_INTELLIGENCE_DB.INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'GOVERNANCE' AND TABLE_TYPE = 'BASE TABLE'
                  AND TABLE_NAME IN ('KPI_REGISTRY', 'KPI_SYNONYM', 'KPI_RELATIONSHIP',
                                     'KPI_DECISION_PROVENANCE'))) AS DETAILS
    UNION ALL
    SELECT 2, 'EXPECTED_REGISTRY_ROWS', IFF((SELECT COUNT(*) FROM KPI_REGISTRY) = 2, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected', 2, 'actual', (SELECT COUNT(*) FROM KPI_REGISTRY))
    UNION ALL
    SELECT 3, 'EXPECTED_CANONICAL_IDENTITIES',
           IFF((SELECT COUNT(DISTINCT METRIC_ID) FROM KPI_REGISTRY) = 2
               AND (SELECT COUNT_IF(METRIC_ID NOT IN ('SALES_BOOKINGS', 'RECOGNIZED_REVENUE'))
                    FROM KPI_REGISTRY) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected', ARRAY_CONSTRUCT('SALES_BOOKINGS', 'RECOGNIZED_REVENUE'))
    UNION ALL
    SELECT 4, 'UNIQUE_REGISTRY_BUSINESS_KEYS',
           IFF((SELECT COUNT(*) FROM KPI_REGISTRY) =
               (SELECT COUNT(DISTINCT METRIC_ID || '|' || METRIC_VERSION) FROM KPI_REGISTRY),
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('key', 'metric_id, metric_version')
    UNION ALL
    SELECT 5, 'BOTH_CERTIFIED',
           IFF((SELECT COUNT_IF(CERTIFICATION_STATUS = 'CERTIFIED') FROM KPI_REGISTRY) = 2,
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('expected_certified', 2)
    UNION ALL
    SELECT 6, 'VALID_CERTIFICATION_STATES',
           IFF((SELECT COUNT_IF(CERTIFICATION_STATUS NOT IN
                   ('DRAFT', 'UNDER_REVIEW', 'CERTIFIED', 'DEPRECATED')) FROM KPI_REGISTRY) = 0,
               'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('allowed', ARRAY_CONSTRUCT('DRAFT', 'UNDER_REVIEW', 'CERTIFIED', 'DEPRECATED'))
    UNION ALL
    SELECT 7, 'VALID_EFFECTIVE_PERIODS',
           IFF((SELECT COUNT_IF(EFFECTIVE_FROM IS NULL OR
                   (EFFECTIVE_TO IS NOT NULL AND EFFECTIVE_TO < EFFECTIVE_FROM))
                FROM KPI_REGISTRY) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('rule', 'effective_to is null or effective_to >= effective_from')
    UNION ALL
    SELECT 8, 'NO_OVERLAPPING_CERTIFIED_VERSIONS',
           IFF((SELECT COUNT(*) FROM KPI_REGISTRY left_version
                JOIN KPI_REGISTRY right_version
                  ON left_version.METRIC_ID = right_version.METRIC_ID
                 AND left_version.METRIC_VERSION < right_version.METRIC_VERSION
                 AND left_version.CERTIFICATION_STATUS = 'CERTIFIED'
                 AND right_version.CERTIFICATION_STATUS = 'CERTIFIED'
                 AND left_version.EFFECTIVE_FROM <= COALESCE(right_version.EFFECTIVE_TO, '9999-12-31'::DATE)
                 AND right_version.EFFECTIVE_FROM <= COALESCE(left_version.EFFECTIVE_TO, '9999-12-31'::DATE)) = 0,
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('expected_overlaps', 0)
    UNION ALL
    SELECT 9, 'REQUIRED_REGISTRY_METADATA',
           IFF((SELECT COUNT_IF(
                   METRIC_NAME IS NULL OR TRIM(METRIC_NAME) = ''
                   OR BUSINESS_DEFINITION IS NULL OR TRIM(BUSINESS_DEFINITION) = ''
                   OR DOMAIN IS NULL OR TRIM(DOMAIN) = ''
                   OR OWNER_ROLE IS NULL OR TRIM(OWNER_ROLE) = ''
                   OR STEWARD_ROLE IS NULL OR TRIM(STEWARD_ROLE) = ''
                   OR CALCULATION_DESCRIPTION IS NULL OR TRIM(CALCULATION_DESCRIPTION) = ''
                   OR TRUSTED_SOURCE_RELATION IS NULL OR TRIM(TRUSTED_SOURCE_RELATION) = ''
                   OR METRIC_AMOUNT_COLUMN IS NULL OR TRIM(METRIC_AMOUNT_COLUMN) = ''
                   OR METRIC_DATE_COLUMN IS NULL OR TRIM(METRIC_DATE_COLUMN) = ''
                   OR APPROVAL_REFERENCE IS NULL OR TRIM(APPROVAL_REFERENCE) = ''
                   OR BUSINESS_REASON IS NULL OR TRIM(BUSINESS_REASON) = ''
               ) FROM KPI_REGISTRY) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected_incomplete_rows', 0)
    UNION ALL
    SELECT 10, 'SALES_REGISTRY_CONTENT',
           IFF((SELECT COUNT_IF(
                   METRIC_ID = 'SALES_BOOKINGS' AND METRIC_VERSION = 1
                   AND METRIC_NAME = 'Sales Bookings' AND DOMAIN = 'SALES'
                   AND BUSINESS_DEFINITION = 'Commercially accepted qualifying customer commitments, including signed booking, cancellation, and amendment events.'
                   AND OWNER_ROLE = 'Sales KPI Owner' AND STEWARD_ROLE = 'Enterprise Data Steward'
                   AND CALCULATION_DESCRIPTION = 'Sum signed amount for immutable BOOKING, CANCELLATION, and AMENDMENT events using event_date for calendar-period attribution.'
                   AND TRUSTED_SOURCE_RELATION = 'KPI_INTELLIGENCE_DB.TRUSTED.FCT_SALES_BOOKINGS'
                   AND METRIC_AMOUNT_COLUMN = 'AMOUNT' AND METRIC_DATE_COLUMN = 'EVENT_DATE'
                   AND CERTIFICATION_STATUS = 'CERTIFIED' AND EFFECTIVE_FROM = '2025-01-01'::DATE
                   AND EFFECTIVE_TO IS NULL AND APPROVAL_REFERENCE = 'I6-SALES-BOOKINGS-V1'
                   AND BUSINESS_REASON = 'Establish an authoritative commercial-demand KPI distinct from Finance recognition.'
                   AND PREDECESSOR_METRIC_ID IS NULL AND PREDECESSOR_METRIC_VERSION IS NULL
                   AND CREATED_AT = '2025-07-01 00:00:00'::TIMESTAMP_NTZ
                   AND UPDATED_AT = '2025-07-01 00:00:00'::TIMESTAMP_NTZ
               ) FROM KPI_REGISTRY) = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('metric_id', 'SALES_BOOKINGS', 'version', 1)
    UNION ALL
    SELECT 11, 'REVENUE_REGISTRY_CONTENT',
           IFF((SELECT COUNT_IF(
                   METRIC_ID = 'RECOGNIZED_REVENUE' AND METRIC_VERSION = 1
                   AND METRIC_NAME = 'Recognized Revenue' AND DOMAIN = 'FINANCE'
                   AND BUSINESS_DEFINITION = 'Value qualifying for recognition under approved management-reporting recognition conditions.'
                   AND OWNER_ROLE = 'Finance KPI Owner' AND STEWARD_ROLE = 'Finance Controller'
                   AND CALCULATION_DESCRIPTION = 'Sum immutable recognition-event amount using recognition_date for calendar-period attribution; retain FULL, PARTIAL, FINAL, and ADJUSTMENT events.'
                   AND TRUSTED_SOURCE_RELATION = 'KPI_INTELLIGENCE_DB.TRUSTED.FCT_RECOGNIZED_REVENUE'
                   AND METRIC_AMOUNT_COLUMN = 'AMOUNT' AND METRIC_DATE_COLUMN = 'RECOGNITION_DATE'
                   AND CERTIFICATION_STATUS = 'CERTIFIED' AND EFFECTIVE_FROM = '2025-01-01'::DATE
                   AND EFFECTIVE_TO IS NULL AND APPROVAL_REFERENCE = 'I6-RECOGNIZED-REVENUE-V1'
                   AND BUSINESS_REASON = 'Establish an authoritative management-reporting recognition KPI distinct from commercial commitments.'
                   AND PREDECESSOR_METRIC_ID IS NULL AND PREDECESSOR_METRIC_VERSION IS NULL
                   AND CREATED_AT = '2025-07-01 00:00:00'::TIMESTAMP_NTZ
                   AND UPDATED_AT = '2025-07-01 00:00:00'::TIMESTAMP_NTZ
               ) FROM KPI_REGISTRY) = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('metric_id', 'RECOGNIZED_REVENUE', 'version', 1)
    UNION ALL
    SELECT 12, 'EXPECTED_SYNONYM_ROWS',
           IFF((SELECT COUNT(*) FROM KPI_SYNONYM) = 9, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected', 9, 'actual', (SELECT COUNT(*) FROM KPI_SYNONYM))
    UNION ALL
    SELECT 13, 'SALES_APPROVED_VOCABULARY',
           IFF((SELECT COUNT(*) FROM KPI_SYNONYM WHERE METRIC_ID = 'SALES_BOOKINGS'
                    AND METRIC_VERSION = 1) = 6
               AND (SELECT COUNT_IF(NORMALIZED_SYNONYM NOT IN
                       ('sales bookings', 'bookings', 'booked sales', 'commercial bookings',
                        'order bookings', 'booked business'))
                    FROM KPI_SYNONYM WHERE METRIC_ID = 'SALES_BOOKINGS' AND METRIC_VERSION = 1) = 0,
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('expected_terms', 6)
    UNION ALL
    SELECT 14, 'REVENUE_APPROVED_VOCABULARY',
           IFF((SELECT COUNT(*) FROM KPI_SYNONYM WHERE METRIC_ID = 'RECOGNIZED_REVENUE'
                    AND METRIC_VERSION = 1) = 3
               AND (SELECT COUNT_IF(NORMALIZED_SYNONYM NOT IN
                       ('recognized revenue', 'revenue', 'finance revenue'))
                    FROM KPI_SYNONYM WHERE METRIC_ID = 'RECOGNIZED_REVENUE' AND METRIC_VERSION = 1) = 0,
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('expected_terms', 3)
    UNION ALL
    SELECT 15, 'REVENUE_HAS_NO_BOOKINGS_SYNONYM',
           IFF((SELECT COUNT_IF(METRIC_ID = 'RECOGNIZED_REVENUE'
                               AND NORMALIZED_SYNONYM = 'bookings') FROM KPI_SYNONYM) = 0,
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('expected', 0)
    UNION ALL
    SELECT 16, 'VALID_SYNONYM_TYPES',
           IFF((SELECT COUNT_IF(SYNONYM_TYPE NOT IN ('CANONICAL_NAME', 'APPROVED_ALIAS'))
                FROM KPI_SYNONYM) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('allowed', ARRAY_CONSTRUCT('CANONICAL_NAME', 'APPROVED_ALIAS'))
    UNION ALL
    SELECT 17, 'NORMALIZED_SYNONYMS_VALID',
           IFF((SELECT COUNT_IF(NORMALIZED_SYNONYM <> LOWER(TRIM(SYNONYM))) FROM KPI_SYNONYM) = 0,
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('rule', 'lower(trim(synonym))')
    UNION ALL
    SELECT 18, 'UNIQUE_SYNONYM_IDS',
           IFF((SELECT COUNT(*) FROM KPI_SYNONYM) =
               (SELECT COUNT(DISTINCT SYNONYM_ID) FROM KPI_SYNONYM), 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('key', 'synonym_id')
    UNION ALL
    SELECT 19, 'UNIQUE_VERSION_SYNONYM_MAPPINGS',
           IFF((SELECT COUNT(*) FROM KPI_SYNONYM) =
               (SELECT COUNT(DISTINCT METRIC_ID || '|' || METRIC_VERSION || '|' || NORMALIZED_SYNONYM)
                FROM KPI_SYNONYM), 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('key', 'metric_id, metric_version, normalized_synonym')
    UNION ALL
    SELECT 20, 'SYNONYMS_REFERENCE_REGISTRY_VERSIONS',
           IFF((SELECT COUNT(*) FROM KPI_SYNONYM synonym
                LEFT JOIN KPI_REGISTRY registry
                  ON registry.METRIC_ID = synonym.METRIC_ID
                 AND registry.METRIC_VERSION = synonym.METRIC_VERSION
                WHERE registry.METRIC_ID IS NULL) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected_orphans', 0)
    UNION ALL
    SELECT 21, 'EXPECTED_SYNONYM_CONTENT',
           IFF((SELECT COUNT(*) FROM expected_synonyms expected
                LEFT JOIN KPI_SYNONYM actual ON actual.SYNONYM_ID = expected.SYNONYM_ID
                WHERE actual.SYNONYM_ID IS NULL
                   OR actual.METRIC_ID <> expected.METRIC_ID
                   OR actual.METRIC_VERSION <> expected.METRIC_VERSION
                   OR actual.SYNONYM <> expected.SYNONYM
                   OR actual.NORMALIZED_SYNONYM <> expected.NORMALIZED_SYNONYM
                   OR actual.SYNONYM_TYPE <> expected.SYNONYM_TYPE
                   OR actual.CREATED_AT <> expected.CREATED_AT) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected_exact_rows', 9)
    UNION ALL
    SELECT 22, 'BOOKINGS_RESOLVES_ONLY_TO_SALES',
           IFF((SELECT COUNT(*) FROM candidate_matches WHERE NORMALIZED_TERM = 'bookings') = 1
               AND (SELECT COUNT_IF(METRIC_ID = 'SALES_BOOKINGS') FROM candidate_matches
                    WHERE NORMALIZED_TERM = 'bookings') = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('term', 'bookings', 'expected', 'SALES_BOOKINGS')
    UNION ALL
    SELECT 23, 'SALES_BOOKINGS_RESOLUTION',
           IFF((SELECT COUNT(*) FROM candidate_matches WHERE NORMALIZED_TERM = 'sales bookings') = 1
               AND (SELECT COUNT_IF(METRIC_ID = 'SALES_BOOKINGS') FROM candidate_matches
                    WHERE NORMALIZED_TERM = 'sales bookings') = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('term', 'sales bookings', 'expected', 'SALES_BOOKINGS')
    UNION ALL
    SELECT 24, 'RECOGNIZED_REVENUE_RESOLUTION',
           IFF((SELECT COUNT(*) FROM candidate_matches WHERE NORMALIZED_TERM = 'recognized revenue') = 1
               AND (SELECT COUNT_IF(METRIC_ID = 'RECOGNIZED_REVENUE') FROM candidate_matches
                    WHERE NORMALIZED_TERM = 'recognized revenue') = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('term', 'recognized revenue', 'expected', 'RECOGNIZED_REVENUE')
    UNION ALL
    SELECT 25, 'REVENUE_RESOLUTION',
           IFF((SELECT COUNT(*) FROM candidate_matches WHERE NORMALIZED_TERM = 'revenue') = 1
               AND (SELECT COUNT_IF(METRIC_ID = 'RECOGNIZED_REVENUE') FROM candidate_matches
                    WHERE NORMALIZED_TERM = 'revenue') = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('term', 'revenue', 'expected', 'RECOGNIZED_REVENUE')
    UNION ALL
    SELECT 26, 'UNKNOWN_TERM_NOT_FOUND',
           IFF((SELECT COUNT(*) FROM candidate_matches WHERE NORMALIZED_TERM = 'unknown term') = 0,
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('term', 'unknown term', 'expected', 'NOT_FOUND')
    UNION ALL
    SELECT 27, 'NON_AUTHORITATIVE_STATUS_EXCLUSION',
           IFF((SELECT COUNT(*) FROM status_negative_controls) = 2
               AND (SELECT COUNT(*) FROM eligible_status_negative_controls) = 0,
               'PASS', 'FAIL'),
           OBJECT_CONSTRUCT(
               'controlled_candidates', (SELECT COUNT(*) FROM status_negative_controls),
               'eligible_candidates', (SELECT COUNT(*) FROM eligible_status_negative_controls),
               'excluded_statuses', ARRAY_CONSTRUCT('DRAFT', 'DEPRECATED')
           )
    UNION ALL
    SELECT 28, 'EXPECTED_RELATIONSHIP_ROWS',
           IFF((SELECT COUNT(*) FROM KPI_RELATIONSHIP) = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected', 1, 'actual', (SELECT COUNT(*) FROM KPI_RELATIONSHIP))
    UNION ALL
    SELECT 29, 'EXPECTED_COMMONLY_CONFUSED_RELATIONSHIP',
           IFF((SELECT COUNT_IF(
                   RELATIONSHIP_ID = 'REL-001'
                   AND SOURCE_METRIC_ID = 'SALES_BOOKINGS'
                   AND TARGET_METRIC_ID = 'RECOGNIZED_REVENUE'
                   AND RELATIONSHIP_TYPE = 'COMMONLY_CONFUSED_WITH'
                   AND RELATIONSHIP_REASON = 'Sales Bookings represents commercial commitment while Recognized Revenue represents Finance recognition. They are frequently compared or confused in enterprise reporting but are distinct certified KPI concepts.'
                   AND CREATED_AT = '2025-07-01 00:00:00'::TIMESTAMP_NTZ
               ) FROM KPI_RELATIONSHIP) = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('relationship_id', 'REL-001')
    UNION ALL
    SELECT 30, 'RELATIONSHIP_ENDPOINTS_EXIST',
           IFF((SELECT COUNT(*) FROM KPI_RELATIONSHIP relationship
                WHERE NOT EXISTS (SELECT 1 FROM KPI_REGISTRY registry
                                  WHERE registry.METRIC_ID = relationship.SOURCE_METRIC_ID)
                   OR NOT EXISTS (SELECT 1 FROM KPI_REGISTRY registry
                                  WHERE registry.METRIC_ID = relationship.TARGET_METRIC_ID)) = 0,
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('expected_orphans', 0)
    UNION ALL
    SELECT 31, 'NO_SELF_RELATIONSHIPS',
           IFF((SELECT COUNT_IF(SOURCE_METRIC_ID = TARGET_METRIC_ID) FROM KPI_RELATIONSHIP) = 0,
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('expected_self_relationships', 0)
    UNION ALL
    SELECT 32, 'VALID_RELATIONSHIP_TYPES',
           IFF((SELECT COUNT_IF(RELATIONSHIP_TYPE <> 'COMMONLY_CONFUSED_WITH')
                FROM KPI_RELATIONSHIP) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('allowed', ARRAY_CONSTRUCT('COMMONLY_CONFUSED_WITH'))
    UNION ALL
    SELECT 33, 'NO_DUPLICATE_SYMMETRIC_RELATIONSHIPS',
           IFF((SELECT COUNT(*) FROM (
                    SELECT LEAST(SOURCE_METRIC_ID, TARGET_METRIC_ID),
                           GREATEST(SOURCE_METRIC_ID, TARGET_METRIC_ID), RELATIONSHIP_TYPE
                    FROM KPI_RELATIONSHIP
                    GROUP BY 1, 2, 3 HAVING COUNT(*) > 1
                ) symmetric_duplicates) = 0, 'PASS', 'FAIL'), OBJECT_CONSTRUCT('expected_duplicates', 0)
    UNION ALL
    SELECT 34, 'NO_REVERSE_DUPLICATE',
           IFF((SELECT COUNT_IF(SOURCE_METRIC_ID = 'RECOGNIZED_REVENUE'
                               AND TARGET_METRIC_ID = 'SALES_BOOKINGS'
                               AND RELATIONSHIP_TYPE = 'COMMONLY_CONFUSED_WITH')
                FROM KPI_RELATIONSHIP) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected_reverse_rows', 0)
    UNION ALL
    SELECT 35, 'RELATIONSHIP_DOES_NOT_CREATE_CANDIDATES',
           IFF((SELECT COUNT(*) FROM candidate_matches
                WHERE NORMALIZED_TERM = 'relationship-only term') = 0
               AND (SELECT COUNT(*) FROM KPI_RELATIONSHIP) = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('term', 'relationship-only term', 'expected', 'NOT_FOUND')
    UNION ALL
    SELECT 36, 'UNDERSPECIFIED_PERFORMANCE_NOT_AUTO_RESOLVED',
           IFF((SELECT COUNT(*) FROM candidate_matches
                WHERE NORMALIZED_TERM = 'how did we perform') = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('term', 'how did we perform', 'expected', 'NOT_FOUND')
    UNION ALL
    SELECT 37, 'EXPECTED_PROVENANCE_ROWS',
           IFF((SELECT COUNT(*) FROM KPI_DECISION_PROVENANCE) = 2, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected', 2, 'actual', (SELECT COUNT(*) FROM KPI_DECISION_PROVENANCE))
    UNION ALL
    SELECT 38, 'UNIQUE_PROVENANCE_IDS',
           IFF((SELECT COUNT(*) FROM KPI_DECISION_PROVENANCE) =
               (SELECT COUNT(DISTINCT PROVENANCE_ID) FROM KPI_DECISION_PROVENANCE),
               'PASS', 'FAIL'), OBJECT_CONSTRUCT('key', 'provenance_id')
    UNION ALL
    SELECT 39, 'PROVENANCE_REFERENCES_REGISTRY',
           IFF((SELECT COUNT(*) FROM KPI_DECISION_PROVENANCE provenance
                LEFT JOIN KPI_REGISTRY registry
                  ON registry.METRIC_ID = provenance.METRIC_ID
                 AND registry.METRIC_VERSION = provenance.METRIC_VERSION
                WHERE registry.METRIC_ID IS NULL) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected_orphans', 0)
    UNION ALL
    SELECT 40, 'CERTIFIED_VERSIONS_HAVE_APPROVAL_PROVENANCE',
           IFF((SELECT COUNT(*) FROM KPI_REGISTRY registry
                WHERE registry.CERTIFICATION_STATUS = 'CERTIFIED'
                  AND NOT EXISTS (
                      SELECT 1 FROM KPI_DECISION_PROVENANCE provenance
                      WHERE provenance.METRIC_ID = registry.METRIC_ID
                        AND provenance.METRIC_VERSION = registry.METRIC_VERSION
                        AND provenance.APPROVAL_REFERENCE = registry.APPROVAL_REFERENCE
                  )) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected_missing_approvals', 0)
    UNION ALL
    SELECT 41, 'EXPECTED_PROVENANCE_CONTENT',
           IFF((SELECT COUNT_IF(
                   PROVENANCE_ID = 'PROV-SB-001' AND METRIC_ID = 'SALES_BOOKINGS'
                   AND METRIC_VERSION = 1 AND DECISION_TYPE = 'INITIAL_CERTIFICATION'
                   AND DECISION_SUMMARY = 'Certify immutable signed commercial events using event_date.'
                   AND RATIONALE = 'Sales Bookings measures accepted commercial commitments. The commercial acceptance or effective event date determines the reporting period. Cancellations and amendments remain separate signed immutable events so history is not rewritten. Recognized Revenue is intentionally excluded because Finance recognition answers a different business question and may occur in another period.'
                   AND APPROVED_BY = 'Enterprise KPI Governance Council'
                   AND APPROVAL_REFERENCE = 'I6-SALES-BOOKINGS-V1'
                   AND DECISION_DATE = '2025-07-01'::DATE AND EFFECTIVE_FROM = '2025-01-01'::DATE
                   AND SUPERSEDES_PROVENANCE_ID IS NULL
                   AND CREATED_AT = '2025-07-01 00:00:00'::TIMESTAMP_NTZ
               ) FROM KPI_DECISION_PROVENANCE) = 1
               AND (SELECT COUNT_IF(
                   PROVENANCE_ID = 'PROV-RR-001' AND METRIC_ID = 'RECOGNIZED_REVENUE'
                   AND METRIC_VERSION = 1 AND DECISION_TYPE = 'INITIAL_CERTIFICATION'
                   AND DECISION_SUMMARY = 'Certify immutable recognition events using recognition_date.'
                   AND RATIONALE = 'Recognized Revenue measures value satisfying approved management-reporting recognition conditions. recognition_date determines the reporting period, which can differ from the commercial booking period. PARTIAL and FINAL events remain separate so staged recognition is preserved and auditable. Sales Bookings is intentionally excluded because a commercial commitment alone does not establish Finance recognition.'
                   AND APPROVED_BY = 'Enterprise KPI Governance Council'
                   AND APPROVAL_REFERENCE = 'I6-RECOGNIZED-REVENUE-V1'
                   AND DECISION_DATE = '2025-07-01'::DATE AND EFFECTIVE_FROM = '2025-01-01'::DATE
                   AND SUPERSEDES_PROVENANCE_ID IS NULL
                   AND CREATED_AT = '2025-07-01 00:00:00'::TIMESTAMP_NTZ
               ) FROM KPI_DECISION_PROVENANCE) = 1, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected', ARRAY_CONSTRUCT('PROV-SB-001', 'PROV-RR-001'))
    UNION ALL
    SELECT 42, 'PROVENANCE_IS_BUSINESS_DECISION_METADATA',
           IFF((SELECT COUNT_IF(
                   DECISION_SUMMARY IS NULL OR TRIM(DECISION_SUMMARY) = ''
                   OR RATIONALE IS NULL OR TRIM(RATIONALE) = ''
                   OR DECISION_TYPE = 'TECHNICAL_LINEAGE'
               ) FROM KPI_DECISION_PROVENANCE) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected_invalid_rows', 0)
    UNION ALL
    SELECT 43, 'NO_UNEXPECTED_FIXTURE_IDENTIFIERS',
           IFF((SELECT COUNT_IF(SYNONYM_ID NOT IN
                   ('SYN-SB-001', 'SYN-SB-002', 'SYN-SB-003', 'SYN-SB-004', 'SYN-SB-005',
                    'SYN-SB-006', 'SYN-RR-001', 'SYN-RR-002', 'SYN-RR-003')) FROM KPI_SYNONYM) = 0
               AND (SELECT COUNT_IF(RELATIONSHIP_ID <> 'REL-001') FROM KPI_RELATIONSHIP) = 0
               AND (SELECT COUNT_IF(PROVENANCE_ID NOT IN ('PROV-SB-001', 'PROV-RR-001'))
                    FROM KPI_DECISION_PROVENANCE) = 0, 'PASS', 'FAIL'),
           OBJECT_CONSTRUCT('expected_synonyms', 9, 'expected_relationships', 1, 'expected_provenance', 2)
)
SELECT CHECK_ID, CHECK_NAME, STATUS, DETAILS
FROM verification
ORDER BY CHECK_ID;
