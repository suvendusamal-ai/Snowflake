-- I7 — Governed Domain Semantic Views
-- Creates bounded Sales and Finance semantic views over certified TRUSTED products.
-- Execute in Snowflake Enterprise only after I5 and I6 have passed.

USE ROLE KPI_PLATFORM_ADMIN;
USE WAREHOUSE KPI_INTELLIGENCE_WH;
USE DATABASE KPI_INTELLIGENCE_DB;

GRANT CREATE SEMANTIC VIEW
    ON SCHEMA KPI_INTELLIGENCE_DB.SEMANTIC
    TO ROLE KPI_SEMANTIC_ENGINEER;

GRANT USAGE
    ON SCHEMA KPI_INTELLIGENCE_DB.SEMANTIC
    TO ROLE KPI_AUDITOR;

USE ROLE KPI_SEMANTIC_ENGINEER;
USE SCHEMA KPI_INTELLIGENCE_DB.SEMANTIC;

CREATE OR REPLACE SEMANTIC VIEW KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW
    TABLES (
        sales_events AS KPI_INTELLIGENCE_DB.TRUSTED.FCT_SALES_BOOKINGS
            PRIMARY KEY (event_id)
            COMMENT = 'Immutable Sales booking, cancellation, and amendment events from the certified TRUSTED Sales product.'
    )
    FACTS (
        PRIVATE sales_events.event_amount AS sales_events.amount
            COMMENT = 'Immutable signed event-level Sales amount. Cancellations remain negative and are never collapsed into prior bookings.'
    )
    DIMENSIONS (
        sales_events.customer_id AS sales_events.customer_id
            COMMENT = 'Customer identifier associated with the Sales event.',
        sales_events.region AS sales_events.region
            COMMENT = 'Governed Sales region associated with the event.',
        sales_events.order_id AS sales_events.order_id
            COMMENT = 'Sales order identifier.',
        sales_events.order_line_id AS sales_events.order_line_id
            COMMENT = 'Sales order line identifier.',
        sales_events.event_type AS sales_events.event_type
            COMMENT = 'Immutable Sales event type preserving BOOKING, CANCELLATION, and AMENDMENT semantics.',
        sales_events.event_date AS sales_events.event_date
            COMMENT = 'Business event date used for Sales Bookings period attribution.',
        sales_events.calendar_year AS sales_events.calendar_year
            COMMENT = 'Calendar year derived from the Sales event date.',
        sales_events.calendar_quarter AS sales_events.calendar_quarter
            COMMENT = 'Calendar quarter derived from the Sales event date.',
        sales_events.currency AS sales_events.currency
            COMMENT = 'Currency code of the Sales event amount.'
    )
    METRICS (
        PUBLIC sales_events.sales_bookings AS SUM(sales_events.event_amount)
            WITH SYNONYMS = (
                'sales bookings',
                'bookings',
                'booked sales',
                'commercial bookings',
                'order bookings',
                'booked business'
            )
            COMMENT = 'Certified KPI SALES_BOOKINGS version 1. Sum of immutable signed Sales event amounts using EVENT_DATE. Approval reference: I6-SALES-BOOKINGS-V1.'
    )
    COMMENT = 'Certified bounded Sales semantic view for SALES_BOOKINGS only. Source: TRUSTED.FCT_SALES_BOOKINGS.';

CREATE OR REPLACE SEMANTIC VIEW KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW
    TABLES (
        revenue_events AS KPI_INTELLIGENCE_DB.TRUSTED.FCT_RECOGNIZED_REVENUE
            PRIMARY KEY (recognition_event_id)
            COMMENT = 'Immutable Finance recognition events from the certified TRUSTED Finance product.'
    )
    FACTS (
        PRIVATE revenue_events.event_amount AS revenue_events.amount
            COMMENT = 'Immutable event-level Finance recognition amount preserving FULL, PARTIAL, FINAL, and ADJUSTMENT semantics.'
    )
    DIMENSIONS (
        revenue_events.customer_id AS revenue_events.customer_id
            COMMENT = 'Customer identifier associated with the recognition event.',
        revenue_events.region AS revenue_events.region
            COMMENT = 'Governed Finance region associated with the recognition event.',
        revenue_events.order_id AS revenue_events.order_id
            COMMENT = 'Order identifier associated with the recognition event.',
        revenue_events.order_line_id AS revenue_events.order_line_id
            COMMENT = 'Order line identifier associated with the recognition event.',
        revenue_events.recognition_type AS revenue_events.recognition_type
            COMMENT = 'Immutable Finance recognition type preserving FULL, PARTIAL, FINAL, and ADJUSTMENT semantics.',
        revenue_events.recognition_date AS revenue_events.recognition_date
            COMMENT = 'Business recognition date used for Recognized Revenue period attribution.',
        revenue_events.calendar_year AS revenue_events.calendar_year
            COMMENT = 'Calendar year derived from the recognition date.',
        revenue_events.calendar_quarter AS revenue_events.calendar_quarter
            COMMENT = 'Calendar quarter derived from the recognition date.',
        revenue_events.currency AS revenue_events.currency
            COMMENT = 'Currency code of the recognition-event amount.'
    )
    METRICS (
        PUBLIC revenue_events.recognized_revenue AS SUM(revenue_events.event_amount)
            WITH SYNONYMS = (
                'recognized revenue',
                'revenue',
                'finance revenue'
            )
            COMMENT = 'Certified KPI RECOGNIZED_REVENUE version 1. Sum of immutable Finance recognition-event amounts using RECOGNITION_DATE. Approval reference: I6-RECOGNIZED-REVENUE-V1.'
    )
    COMMENT = 'Certified bounded Finance semantic view for RECOGNIZED_REVENUE only. Source: TRUSTED.FCT_RECOGNIZED_REVENUE.';

USE ROLE KPI_PLATFORM_ADMIN;

GRANT REFERENCES, SELECT
    ON SEMANTIC VIEW KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW
    TO ROLE KPI_AI_BUILDER;

GRANT REFERENCES, SELECT
    ON SEMANTIC VIEW KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW
    TO ROLE KPI_AI_BUILDER;

GRANT REFERENCES, SELECT
    ON SEMANTIC VIEW KPI_INTELLIGENCE_DB.SEMANTIC.SALES_KPI_SEMANTIC_VIEW
    TO ROLE KPI_AUDITOR;

GRANT REFERENCES, SELECT
    ON SEMANTIC VIEW KPI_INTELLIGENCE_DB.SEMANTIC.FINANCE_KPI_SEMANTIC_VIEW
    TO ROLE KPI_AUDITOR;
