-- I7 — Governed Domain Semantic Views verification
-- Read-only verification. Returns one row per check; every row must report PASS.

USE ROLE KPI_PLATFORM_ADMIN;
USE WAREHOUSE KPI_INTELLIGENCE_WH;
USE DATABASE KPI_INTELLIGENCE_DB;
USE SCHEMA KPI_INTELLIGENCE_DB.SEMANTIC;

WITH
semantic_view_metadata AS (
    SELECT name, owner
    FROM KPI_INTELLIGENCE_DB.INFORMATION_SCHEMA.SEMANTIC_VIEWS
    WHERE schema = 'SEMANTIC'
      AND name IN ('SALES_KPI_SEMANTIC_VIEW', 'FINANCE_KPI_SEMANTIC_VIEW')
),
semantic_table_metadata AS (
    SELECT semantic_view_name, name, base_table_schema, base_table_name
    FROM KPI_INTELLIGENCE_DB.INFORMATION_SCHEMA.SEMANTIC_TABLES
    WHERE semantic_view_schema = 'SEMANTIC'
      AND semantic_view_name IN ('SALES_KPI_SEMANTIC_VIEW', 'FINANCE_KPI_SEMANTIC_VIEW')
),
semantic_dimension_metadata AS (
    SELECT semantic_view_name, table_name, name, expression
    FROM KPI_INTELLIGENCE_DB.INFORMATION_SCHEMA.SEMANTIC_DIMENSIONS
    WHERE semantic_view_schema = 'SEMANTIC'
      AND semantic_view_name IN ('SALES_KPI_SEMANTIC_VIEW', 'FINANCE_KPI_SEMANTIC_VIEW')
),
semantic_metric_metadata AS (
    SELECT semantic_view_name, table_name, name, expression, synonyms, comment
    FROM KPI_INTELLIGENCE_DB.INFORMATION_SCHEMA.SEMANTIC_METRICS
    WHERE semantic_view_schema = 'SEMANTIC'
      AND semantic_view_name IN ('SALES_KPI_SEMANTIC_VIEW', 'FINANCE_KPI_SEMANTIC_VIEW')
),
semantic_relationship_metadata AS (
    SELECT semantic_view_name
    FROM KPI_INTELLIGENCE_DB.INFORMATION_SCHEMA.SEMANTIC_RELATIONSHIPS
    WHERE semantic_view_schema = 'SEMANTIC'
      AND semantic_view_name IN ('SALES_KPI_SEMANTIC_VIEW', 'FINANCE_KPI_SEMANTIC_VIEW')
),
sales_registry AS (
    SELECT metric_id, metric_version, trusted_source_relation, metric_amount_column,
           metric_date_column, certification_status, effective_from, effective_to,
           approval_reference
    FROM KPI_INTELLIGENCE_DB.GOVERNANCE.KPI_REGISTRY
    WHERE metric_id = 'SALES_BOOKINGS'
      AND metric_version = 1
),
revenue_registry AS (
    SELECT metric_id, metric_version, trusted_source_relation, metric_amount_column,
           metric_date_column, certification_status, effective_from, effective_to,
           approval_reference
    FROM KPI_INTELLIGENCE_DB.GOVERNANCE.KPI_REGISTRY
    WHERE metric_id = 'RECOGNIZED_REVENUE'
      AND metric_version = 1
),
sales_governed_synonyms AS (
    SELECT LOWER(synonym) AS synonym
    FROM KPI_INTELLIGENCE_DB.GOVERNANCE.KPI_SYNONYM
    WHERE metric_id = 'SALES_BOOKINGS'
      AND metric_version = 1
),
revenue_governed_synonyms AS (
    SELECT LOWER(synonym) AS synonym
    FROM KPI_INTELLIGENCE_DB.GOVERNANCE.KPI_SYNONYM
    WHERE metric_id = 'RECOGNIZED_REVENUE'
      AND metric_version = 1
),
sales_semantic_synonyms AS (
    SELECT LOWER(TRIM(flattened.value::VARCHAR)) AS synonym
    FROM semantic_metric_metadata AS metric,
         LATERAL FLATTEN(INPUT => metric.synonyms) AS flattened
    WHERE metric.semantic_view_name = 'SALES_KPI_SEMANTIC_VIEW'
      AND metric.name = 'SALES_BOOKINGS'
),
revenue_semantic_synonyms AS (
    SELECT LOWER(TRIM(flattened.value::VARCHAR)) AS synonym
    FROM semantic_metric_metadata AS metric,
         LATERAL FLATTEN(INPUT => metric.synonyms) AS flattened
    WHERE metric.semantic_view_name = 'FINANCE_KPI_SEMANTIC_VIEW'
      AND metric.name = 'RECOGNIZED_REVENUE'
),
sales_q1_semantic AS (
    SELECT sales_bookings
    FROM SEMANTIC_VIEW(
        KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW
        METRICS sales_events.sales_bookings
        WHERE sales_events.event_date >= '2025-01-01'::DATE
          AND sales_events.event_date < '2025-04-01'::DATE
    )
),
sales_q2_semantic AS (
    SELECT sales_bookings
    FROM SEMANTIC_VIEW(
        KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW
        METRICS sales_events.sales_bookings
        WHERE sales_events.event_date >= '2025-04-01'::DATE
          AND sales_events.event_date < '2025-07-01'::DATE
    )
),
sales_h1_semantic AS (
    SELECT sales_bookings
    FROM SEMANTIC_VIEW(
        KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW
        METRICS sales_events.sales_bookings
        WHERE sales_events.event_date >= '2025-01-01'::DATE
          AND sales_events.event_date < '2025-07-01'::DATE
    )
),
revenue_q1_semantic AS (
    SELECT recognized_revenue
    FROM SEMANTIC_VIEW(
        KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW
        METRICS revenue_events.recognized_revenue
        WHERE revenue_events.recognition_date >= '2025-01-01'::DATE
          AND revenue_events.recognition_date < '2025-04-01'::DATE
    )
),
revenue_q2_semantic AS (
    SELECT recognized_revenue
    FROM SEMANTIC_VIEW(
        KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW
        METRICS revenue_events.recognized_revenue
        WHERE revenue_events.recognition_date >= '2025-04-01'::DATE
          AND revenue_events.recognition_date < '2025-07-01'::DATE
    )
),
revenue_h1_semantic AS (
    SELECT recognized_revenue
    FROM SEMANTIC_VIEW(
        KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW
        METRICS revenue_events.recognized_revenue
        WHERE revenue_events.recognition_date >= '2025-01-01'::DATE
          AND revenue_events.recognition_date < '2025-07-01'::DATE
    )
),
sales_trusted AS (
    SELECT
        SUM(IFF(event_date >= '2025-01-01'::DATE AND event_date < '2025-04-01'::DATE, amount, 0)) AS q1,
        SUM(IFF(event_date >= '2025-04-01'::DATE AND event_date < '2025-07-01'::DATE, amount, 0)) AS q2,
        SUM(IFF(event_date >= '2025-01-01'::DATE AND event_date < '2025-07-01'::DATE, amount, 0)) AS h1
    FROM KPI_INTELLIGENCE_DB.TRUSTED.FCT_SALES_BOOKINGS
),
revenue_trusted AS (
    SELECT
        SUM(IFF(recognition_date >= '2025-01-01'::DATE AND recognition_date < '2025-04-01'::DATE, amount, 0)) AS q1,
        SUM(IFF(recognition_date >= '2025-04-01'::DATE AND recognition_date < '2025-07-01'::DATE, amount, 0)) AS q2,
        SUM(IFF(recognition_date >= '2025-01-01'::DATE AND recognition_date < '2025-07-01'::DATE, amount, 0)) AS h1
    FROM KPI_INTELLIGENCE_DB.TRUSTED.FCT_RECOGNIZED_REVENUE
),
o300_semantic AS (
    SELECT event_type, sales_bookings
    FROM SEMANTIC_VIEW(
        KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW
        METRICS sales_events.sales_bookings
        DIMENSIONS sales_events.event_type
        WHERE sales_events.order_id = 'O300'
    )
),
o400_semantic AS (
    SELECT recognition_type, calendar_quarter, recognized_revenue
    FROM SEMANTIC_VIEW(
        KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW
        METRICS revenue_events.recognized_revenue
        DIMENSIONS revenue_events.recognition_type, revenue_events.calendar_quarter
        WHERE revenue_events.order_id = 'O400'
    )
),
checks AS (
    SELECT 'SEMANTIC_VIEW_COUNT' AS check_name,
           IFF((SELECT COUNT(*) FROM semantic_view_metadata) = 2, 'PASS', 'FAIL') AS status,
           'Expected exactly two governed domain semantic views.' AS detail
    UNION ALL
    SELECT 'SEMANTIC_VIEW_OWNERSHIP',
           IFF((SELECT COUNT(*) FROM semantic_view_metadata WHERE owner = 'KPI_SEMANTIC_ENGINEER') = 2, 'PASS', 'FAIL'),
           'Both semantic views must be owned by KPI_SEMANTIC_ENGINEER.'
    UNION ALL
    SELECT 'SALES_SINGLE_TRUSTED_SOURCE',
           IFF((SELECT COUNT(*) FROM semantic_table_metadata
                WHERE semantic_view_name = 'SALES_KPI_SEMANTIC_VIEW'
                  AND base_table_schema = 'TRUSTED'
                  AND base_table_name = 'FCT_SALES_BOOKINGS') = 1
               AND (SELECT COUNT(*) FROM semantic_table_metadata
                    WHERE semantic_view_name = 'SALES_KPI_SEMANTIC_VIEW') = 1, 'PASS', 'FAIL'),
           'Sales semantic view must use only TRUSTED.FCT_SALES_BOOKINGS.'
    UNION ALL
    SELECT 'FINANCE_SINGLE_TRUSTED_SOURCE',
           IFF((SELECT COUNT(*) FROM semantic_table_metadata
                WHERE semantic_view_name = 'FINANCE_KPI_SEMANTIC_VIEW'
                  AND base_table_schema = 'TRUSTED'
                  AND base_table_name = 'FCT_RECOGNIZED_REVENUE') = 1
               AND (SELECT COUNT(*) FROM semantic_table_metadata
                    WHERE semantic_view_name = 'FINANCE_KPI_SEMANTIC_VIEW') = 1, 'PASS', 'FAIL'),
           'Finance semantic view must use only TRUSTED.FCT_RECOGNIZED_REVENUE.'
    UNION ALL
    SELECT 'NO_SEMANTIC_RELATIONSHIPS',
           IFF((SELECT COUNT(*) FROM semantic_relationship_metadata) = 0, 'PASS', 'FAIL'),
           'No cross-domain or other semantic relationship is permitted.'
    UNION ALL
    SELECT 'SALES_EXACT_DIMENSION_SET',
           IFF((SELECT COUNT(*) FROM semantic_dimension_metadata
                WHERE semantic_view_name = 'SALES_KPI_SEMANTIC_VIEW') = 9
               AND (SELECT COUNT(*) FROM semantic_dimension_metadata
                    WHERE semantic_view_name = 'SALES_KPI_SEMANTIC_VIEW'
                      AND name IN ('CUSTOMER_ID', 'REGION', 'ORDER_ID', 'ORDER_LINE_ID', 'EVENT_TYPE',
                                   'EVENT_DATE', 'CALENDAR_YEAR', 'CALENDAR_QUARTER', 'CURRENCY')) = 9,
               'PASS', 'FAIL'),
           'Sales exposes only the approved nine dimensions.'
    UNION ALL
    SELECT 'FINANCE_EXACT_DIMENSION_SET',
           IFF((SELECT COUNT(*) FROM semantic_dimension_metadata
                WHERE semantic_view_name = 'FINANCE_KPI_SEMANTIC_VIEW') = 9
               AND (SELECT COUNT(*) FROM semantic_dimension_metadata
                    WHERE semantic_view_name = 'FINANCE_KPI_SEMANTIC_VIEW'
                      AND name IN ('CUSTOMER_ID', 'REGION', 'ORDER_ID', 'ORDER_LINE_ID', 'RECOGNITION_TYPE',
                                   'RECOGNITION_DATE', 'CALENDAR_YEAR', 'CALENDAR_QUARTER', 'CURRENCY')) = 9,
               'PASS', 'FAIL'),
           'Finance exposes only the approved nine dimensions.'
    UNION ALL
    SELECT 'SALES_SINGLE_CANONICAL_METRIC',
           IFF((SELECT COUNT(*) FROM semantic_metric_metadata
                WHERE semantic_view_name = 'SALES_KPI_SEMANTIC_VIEW'
                  AND name = 'SALES_BOOKINGS'
                  AND UPPER(expression) LIKE '%SUM(%'
                  AND UPPER(expression) LIKE '%EVENT_AMOUNT%') = 1
               AND (SELECT COUNT(*) FROM semantic_metric_metadata
                    WHERE semantic_view_name = 'SALES_KPI_SEMANTIC_VIEW') = 1, 'PASS', 'FAIL'),
           'Sales exposes only SALES_BOOKINGS as SUM of immutable event amount.'
    UNION ALL
    SELECT 'FINANCE_SINGLE_CANONICAL_METRIC',
           IFF((SELECT COUNT(*) FROM semantic_metric_metadata
                WHERE semantic_view_name = 'FINANCE_KPI_SEMANTIC_VIEW'
                  AND name = 'RECOGNIZED_REVENUE'
                  AND UPPER(expression) LIKE '%SUM(%'
                  AND UPPER(expression) LIKE '%EVENT_AMOUNT%') = 1
               AND (SELECT COUNT(*) FROM semantic_metric_metadata
                    WHERE semantic_view_name = 'FINANCE_KPI_SEMANTIC_VIEW') = 1, 'PASS', 'FAIL'),
           'Finance exposes only RECOGNIZED_REVENUE as SUM of immutable recognition-event amount.'
    UNION ALL
    SELECT 'SALES_EVENT_DATE_ATTRIBUTION',
           IFF((SELECT COUNT(*) FROM semantic_dimension_metadata
                WHERE semantic_view_name = 'SALES_KPI_SEMANTIC_VIEW'
                  AND name = 'EVENT_DATE'
                  AND UPPER(expression) LIKE '%EVENT_DATE%') = 1, 'PASS', 'FAIL'),
           'Sales time attribution is EVENT_DATE.'
    UNION ALL
    SELECT 'FINANCE_RECOGNITION_DATE_ATTRIBUTION',
           IFF((SELECT COUNT(*) FROM semantic_dimension_metadata
                WHERE semantic_view_name = 'FINANCE_KPI_SEMANTIC_VIEW'
                  AND name = 'RECOGNITION_DATE'
                  AND UPPER(expression) LIKE '%RECOGNITION_DATE%') = 1, 'PASS', 'FAIL'),
           'Finance time attribution is RECOGNITION_DATE.'
    UNION ALL
    SELECT 'SALES_CERTIFIED_REGISTRY_MAPPING',
           IFF((SELECT COUNT(*) FROM sales_registry
                WHERE trusted_source_relation = 'KPI_INTELLIGENCE_DB.TRUSTED.FCT_SALES_BOOKINGS'
                  AND metric_amount_column = 'AMOUNT'
                  AND metric_date_column = 'EVENT_DATE'
                  AND certification_status = 'CERTIFIED'
                  AND effective_from <= CURRENT_DATE()
                  AND (effective_to IS NULL OR effective_to >= CURRENT_DATE())) = 1, 'PASS', 'FAIL'),
           'Sales semantic view maps to the current certified I6 contract.'
    UNION ALL
    SELECT 'FINANCE_CERTIFIED_REGISTRY_MAPPING',
           IFF((SELECT COUNT(*) FROM revenue_registry
                WHERE trusted_source_relation = 'KPI_INTELLIGENCE_DB.TRUSTED.FCT_RECOGNIZED_REVENUE'
                  AND metric_amount_column = 'AMOUNT'
                  AND metric_date_column = 'RECOGNITION_DATE'
                  AND certification_status = 'CERTIFIED'
                  AND effective_from <= CURRENT_DATE()
                  AND (effective_to IS NULL OR effective_to >= CURRENT_DATE())) = 1, 'PASS', 'FAIL'),
           'Finance semantic view maps to the current certified I6 contract.'
    UNION ALL
    SELECT 'SALES_METRIC_GOVERNANCE_METADATA',
           IFF((SELECT COUNT(*) FROM semantic_metric_metadata
                WHERE semantic_view_name = 'SALES_KPI_SEMANTIC_VIEW'
                  AND name = 'SALES_BOOKINGS'
                  AND UPPER(comment) LIKE '%SALES_BOOKINGS%'
                  AND UPPER(comment) LIKE '%VERSION 1%'
                  AND UPPER(comment) LIKE '%I6-SALES-BOOKINGS-V1%'
                  AND UPPER(comment) LIKE '%' || (SELECT UPPER(approval_reference) FROM sales_registry) || '%') = 1,
               'PASS', 'FAIL'),
           'Sales metric metadata carries KPI identity, version, and approval reference.'
    UNION ALL
    SELECT 'FINANCE_METRIC_GOVERNANCE_METADATA',
           IFF((SELECT COUNT(*) FROM semantic_metric_metadata
                WHERE semantic_view_name = 'FINANCE_KPI_SEMANTIC_VIEW'
                  AND name = 'RECOGNIZED_REVENUE'
                  AND UPPER(comment) LIKE '%RECOGNIZED_REVENUE%'
                  AND UPPER(comment) LIKE '%VERSION 1%'
                  AND UPPER(comment) LIKE '%I6-RECOGNIZED-REVENUE-V1%'
                  AND UPPER(comment) LIKE '%' || (SELECT UPPER(approval_reference) FROM revenue_registry) || '%') = 1,
               'PASS', 'FAIL'),
           'Finance metric metadata carries KPI identity, version, and approval reference.'
    UNION ALL
    SELECT 'SALES_EXACT_VOCABULARY',
           IFF(NOT EXISTS (
                   SELECT synonym FROM sales_governed_synonyms
                   MINUS
                   SELECT synonym FROM sales_semantic_synonyms
               )
               AND NOT EXISTS (
                   SELECT synonym FROM sales_semantic_synonyms
                   MINUS
                   SELECT synonym FROM sales_governed_synonyms
               ),
               'PASS', 'FAIL'),
           'Sales semantic synonyms exactly match the six governed I6 synonyms.'
    UNION ALL
    SELECT 'FINANCE_EXACT_VOCABULARY',
           IFF(NOT EXISTS (
                   SELECT synonym FROM revenue_governed_synonyms
                   MINUS
                   SELECT synonym FROM revenue_semantic_synonyms
               )
               AND NOT EXISTS (
                   SELECT synonym FROM revenue_semantic_synonyms
                   MINUS
                   SELECT synonym FROM revenue_governed_synonyms
               ),
               'PASS', 'FAIL'),
           'Finance semantic synonyms exactly match the three governed I6 synonyms.'
    UNION ALL
    SELECT 'PROHIBITED_BOOKINGS_TO_REVENUE_ABSENT',
           IFF(NOT EXISTS (
                   SELECT 1
                   FROM revenue_semantic_synonyms
                   WHERE synonym = 'bookings'
               ),
               'PASS', 'FAIL'),
           'The prohibited bookings synonym is absent from Recognized Revenue.'
    UNION ALL
    SELECT 'SALES_Q1_SEMANTIC_EQUALS_TRUSTED_EQUALS_FIXTURE',
           IFF((SELECT sales_bookings FROM sales_q1_semantic) = 4900
               AND (SELECT q1 FROM sales_trusted) = 4900, 'PASS', 'FAIL'),
           '2025 Q1 Sales Bookings equals 4900 in semantic and TRUSTED layers.'
    UNION ALL
    SELECT 'SALES_Q2_SEMANTIC_EQUALS_TRUSTED_EQUALS_FIXTURE',
           IFF((SELECT sales_bookings FROM sales_q2_semantic) = 900
               AND (SELECT q2 FROM sales_trusted) = 900, 'PASS', 'FAIL'),
           '2025 Q2 Sales Bookings equals 900 in semantic and TRUSTED layers.'
    UNION ALL
    SELECT 'SALES_H1_SEMANTIC_EQUALS_TRUSTED_EQUALS_FIXTURE',
           IFF((SELECT sales_bookings FROM sales_h1_semantic) = 5800
               AND (SELECT h1 FROM sales_trusted) = 5800, 'PASS', 'FAIL'),
           '2025 H1 Sales Bookings equals 5800 in semantic and TRUSTED layers.'
    UNION ALL
    SELECT 'REVENUE_Q1_SEMANTIC_EQUALS_TRUSTED_EQUALS_FIXTURE',
           IFF((SELECT recognized_revenue FROM revenue_q1_semantic) = 1800
               AND (SELECT q1 FROM revenue_trusted) = 1800, 'PASS', 'FAIL'),
           '2025 Q1 Recognized Revenue equals 1800 in semantic and TRUSTED layers.'
    UNION ALL
    SELECT 'REVENUE_Q2_SEMANTIC_EQUALS_TRUSTED_EQUALS_FIXTURE',
           IFF((SELECT recognized_revenue FROM revenue_q2_semantic) = 4000
               AND (SELECT q2 FROM revenue_trusted) = 4000, 'PASS', 'FAIL'),
           '2025 Q2 Recognized Revenue equals 4000 in semantic and TRUSTED layers.'
    UNION ALL
    SELECT 'REVENUE_H1_SEMANTIC_EQUALS_TRUSTED_EQUALS_FIXTURE',
           IFF((SELECT recognized_revenue FROM revenue_h1_semantic) = 5800
               AND (SELECT h1 FROM revenue_trusted) = 5800, 'PASS', 'FAIL'),
           '2025 H1 Recognized Revenue equals 5800 in semantic and TRUSTED layers.'
    UNION ALL
    SELECT 'O300_IMMUTABLE_CANCELLATION_BEHAVIOR',
           IFF((SELECT COUNT(*) FROM o300_semantic) = 2
               AND (SELECT COUNT(*) FROM o300_semantic WHERE event_type = 'BOOKING' AND sales_bookings = 800) = 1
               AND (SELECT COUNT(*) FROM o300_semantic WHERE event_type = 'CANCELLATION' AND sales_bookings = -800) = 1
               AND (SELECT COUNT(*) FROM KPI_INTELLIGENCE_DB.TRUSTED.FCT_SALES_BOOKINGS
                    WHERE order_id = 'O300') = 2, 'PASS', 'FAIL'),
           'O300 remains two immutable signed semantic events: +800 booking and -800 cancellation.'
    UNION ALL
    SELECT 'O400_PARTIAL_RECOGNITION_BEHAVIOR',
           IFF((SELECT COUNT(*) FROM o400_semantic) = 2
               AND (SELECT COUNT(*) FROM o400_semantic
                    WHERE recognition_type = 'PARTIAL' AND calendar_quarter = 'Q1'
                      AND recognized_revenue = 800) = 1
               AND (SELECT COUNT(*) FROM o400_semantic
                    WHERE recognition_type = 'FINAL' AND calendar_quarter = 'Q2'
                      AND recognized_revenue = 1200) = 1
               AND (SELECT COUNT(*) FROM KPI_INTELLIGENCE_DB.TRUSTED.FCT_RECOGNIZED_REVENUE
                    WHERE order_id = 'O400') = 2
               AND (SELECT SUM(recognized_revenue) FROM o400_semantic) = 2000,
               'PASS', 'FAIL'),
           'O400 remains two Finance recognition events: Q1 PARTIAL 800, Q2 FINAL 1200, H1 2000.'
)
SELECT check_name, status, detail
FROM checks
ORDER BY check_name;

-- Consumer grants are verified from each role's actual grant set.
SHOW GRANTS TO ROLE KPI_AI_BUILDER;

SELECT
    'KPI_AI_BUILDER_SEMANTIC_VIEW_READ_ONLY_ACCESS' AS check_name,
    IFF(
        COUNT_IF("privilege" IN ('REFERENCES', 'SELECT')
                 AND "name" IN (
                     'KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW',
                     'KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW'
                 )) = 4
        AND COUNT_IF("privilege" NOT IN ('REFERENCES', 'SELECT', 'USAGE')
                     AND "name" IN (
                         'KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW',
                         'KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW'
                     )) = 0,
        'PASS', 'FAIL'
    ) AS status,
    'KPI_AI_BUILDER has REFERENCES and SELECT, with no write privilege, on both semantic views.' AS detail
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));

SHOW GRANTS TO ROLE KPI_AUDITOR;

SELECT
    'KPI_AUDITOR_SEMANTIC_VIEW_READ_ONLY_ACCESS' AS check_name,
    IFF(
        COUNT_IF("privilege" IN ('REFERENCES', 'SELECT')
                 AND "name" IN (
                     'KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW',
                     'KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW'
                 )) = 4
        AND COUNT_IF("privilege" NOT IN ('REFERENCES', 'SELECT', 'USAGE')
                     AND "name" IN (
                         'KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW',
                         'KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW'
                     )) = 0,
        'PASS', 'FAIL'
    ) AS status,
    'KPI_AUDITOR has REFERENCES and SELECT, with no write privilege, on both semantic views.' AS detail
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()));
