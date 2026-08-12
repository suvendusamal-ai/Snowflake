-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Ingestion Pipeline: Tasks + Stream-driven processing
-- ============================================================================

USE ROLE CORTEX_AI_ADMIN;
USE DATABASE CORTEX_AI_PLATFORM;
USE WAREHOUSE CORTEX_AI_INGESTION_WH;

-- ============================================================================
-- Stored Procedure: Process a single document through the full pipeline
-- Called by the ingestion task for each new document in the stream
-- ============================================================================
CREATE OR REPLACE PROCEDURE RAW.PROCESS_DOCUMENT_PIPELINE(DOCUMENT_ID VARCHAR)
RETURNS VARIANT
LANGUAGE SQL
EXECUTE AS CALLER
AS
BEGIN
    LET v_stage_path VARCHAR;
    LET v_file_type VARCHAR;
    LET v_file_name VARCHAR;
    LET v_department VARCHAR;
    LET v_parsed_content VARCHAR;
    LET v_classification VARIANT;
    LET v_word_count NUMBER;
    LET v_result VARIANT;

    -- Fetch document info
    SELECT STAGE_PATH, FILE_TYPE, FILE_NAME, DEPARTMENT
    INTO :v_stage_path, :v_file_type, :v_file_name, :v_department
    FROM RAW.DOCUMENT_REGISTRY
    WHERE DOCUMENT_ID = :DOCUMENT_ID;

    -- Step 1: Parse document
    UPDATE RAW.DOCUMENT_REGISTRY
    SET PROCESSING_STATUS = 'PARSING', LAST_PROCESSED_AT = CURRENT_TIMESTAMP()
    WHERE DOCUMENT_ID = :DOCUMENT_ID;

    BEGIN
        -- Use AI_PARSE_DOCUMENT for supported types
        IF (:v_file_type IN ('.pdf', '.docx', '.pptx', '.xlsx', '.html')) THEN
            LET v_parse_result VARIANT;
            SELECT AI_PARSE_DOCUMENT(
                BUILD_SCOPED_FILE_URL(:v_stage_path),
                'LAYOUT'
            ) INTO :v_parse_result;
            LET v_parsed_content := v_parse_result:content::VARCHAR;
        ELSEIF (:v_file_type IN ('.png', '.jpg')) THEN
            SELECT AI_PARSE_DOCUMENT(
                BUILD_SCOPED_FILE_URL(:v_stage_path),
                'OCR'
            ):content::VARCHAR INTO :v_parsed_content;
        ELSE
            -- Direct text read for .txt, .csv, .json
            LET v_parsed_content := 'TEXT_DIRECT_READ_PLACEHOLDER';
        END IF;

        LET v_word_count := ARRAY_SIZE(SPLIT(:v_parsed_content, ' '));

        INSERT INTO PROCESSED.PARSED_DOCUMENTS (
            DOCUMENT_ID, PARSED_CONTENT, WORD_COUNT, PARSE_MODEL
        ) VALUES (
            :DOCUMENT_ID, :v_parsed_content, :v_word_count, 'ai_parse_document'
        );

    EXCEPTION
        WHEN OTHER THEN
            UPDATE RAW.DOCUMENT_REGISTRY
            SET PROCESSING_STATUS = 'FAILED',
                ERROR_MESSAGE = :SQLERRM,
                RETRY_COUNT = RETRY_COUNT + 1
            WHERE DOCUMENT_ID = :DOCUMENT_ID;
            RETURN OBJECT_CONSTRUCT('status', 'FAILED', 'step', 'PARSE', 'error', :SQLERRM);
    END;

    -- Step 2: Classify document
    UPDATE RAW.DOCUMENT_REGISTRY
    SET PROCESSING_STATUS = 'CLASSIFYING'
    WHERE DOCUMENT_ID = :DOCUMENT_ID;

    BEGIN
        LET v_preview VARCHAR := LEFT(:v_parsed_content, 2000);
        LET v_class_prompt VARCHAR := 'Classify this document. Department options: finance, treasury, procurement, risk, compliance, audit, hr, legal, operations. Document type options: policy, report, memo, contract, procedure, manual, form, correspondence. Sensitivity options: public, internal, confidential, restricted. File: ' || :v_file_name || '. Content: ' || :v_preview || '. Return ONLY JSON: {"department":"...","document_type":"...","sensitivity":"...","topics":["..."]}';

        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            'claude-3-5-haiku',
            :v_class_prompt
        ) INTO :v_classification;

        -- Parse classification (best-effort)
        LET v_dept VARCHAR := COALESCE(TRY_PARSE_JSON(:v_classification):department::VARCHAR, :v_department);
        LET v_doc_type VARCHAR := COALESCE(TRY_PARSE_JSON(:v_classification):document_type::VARCHAR, 'report');
        LET v_sensitivity VARCHAR := COALESCE(TRY_PARSE_JSON(:v_classification):sensitivity::VARCHAR, 'internal');

        INSERT INTO PROCESSED.DOCUMENT_CLASSIFICATIONS (
            DOCUMENT_ID, DEPARTMENT, DOCUMENT_TYPE, SENSITIVITY_LEVEL,
            CONFIDENCE_SCORE, CLASSIFICATION_MODEL
        ) VALUES (
            :DOCUMENT_ID, :v_dept, :v_doc_type, :v_sensitivity,
            0.85, 'claude-3-5-haiku'
        );

    EXCEPTION
        WHEN OTHER THEN
            -- Classification failure is non-fatal; use original department
            INSERT INTO PROCESSED.DOCUMENT_CLASSIFICATIONS (
                DOCUMENT_ID, DEPARTMENT, DOCUMENT_TYPE, SENSITIVITY_LEVEL,
                CONFIDENCE_SCORE, CLASSIFICATION_MODEL
            ) VALUES (
                :DOCUMENT_ID, :v_department, 'report', 'internal', 0.3, 'fallback'
            );
    END;

    -- Step 3: Mark complete
    UPDATE RAW.DOCUMENT_REGISTRY
    SET PROCESSING_STATUS = 'COMPLETED', LAST_PROCESSED_AT = CURRENT_TIMESTAMP()
    WHERE DOCUMENT_ID = :DOCUMENT_ID;

    -- Log to processing log
    INSERT INTO PROCESSED.PROCESSING_LOG (
        DOCUMENT_ID, STEP_NAME, STATUS, COMPLETED_AT
    ) VALUES (
        :DOCUMENT_ID, 'FULL_PIPELINE', 'SUCCESS', CURRENT_TIMESTAMP()
    );

    RETURN OBJECT_CONSTRUCT(
        'status', 'COMPLETED',
        'document_id', :DOCUMENT_ID,
        'word_count', :v_word_count
    );
END;

-- ============================================================================
-- Task: Process new documents from stream (runs every 1 minute)
-- ============================================================================
CREATE OR REPLACE TASK RAW.DOCUMENT_INGESTION_TASK
    WAREHOUSE = CORTEX_AI_INGESTION_WH
    SCHEDULE = '1 MINUTE'
    COMMENT = 'Processes new documents detected in DOCUMENT_REGISTRY_STREAM'
    WHEN SYSTEM$STREAM_HAS_DATA('RAW.DOCUMENT_REGISTRY_STREAM')
AS
DECLARE
    c1 CURSOR FOR
        SELECT DOCUMENT_ID FROM RAW.DOCUMENT_REGISTRY_STREAM
        WHERE PROCESSING_STATUS = 'PENDING';
BEGIN
    FOR rec IN c1 DO
        CALL RAW.PROCESS_DOCUMENT_PIPELINE(rec.DOCUMENT_ID);
    END FOR;
END;

-- ============================================================================
-- Retry task: Re-process failed documents (runs every 15 minutes)
-- ============================================================================
CREATE OR REPLACE TASK RAW.DOCUMENT_RETRY_TASK
    WAREHOUSE = CORTEX_AI_INGESTION_WH
    SCHEDULE = '15 MINUTE'
    COMMENT = 'Retries failed documents with retry_count < 3'
AS
DECLARE
    c1 CURSOR FOR
        SELECT DOCUMENT_ID FROM RAW.DOCUMENT_REGISTRY
        WHERE PROCESSING_STATUS = 'FAILED' AND RETRY_COUNT < 3;
BEGIN
    FOR rec IN c1 DO
        CALL RAW.PROCESS_DOCUMENT_PIPELINE(rec.DOCUMENT_ID);
    END FOR;
END;

-- Enable tasks (commented out for safety - uncomment during deployment)
-- ALTER TASK RAW.DOCUMENT_INGESTION_TASK RESUME;
-- ALTER TASK RAW.DOCUMENT_RETRY_TASK RESUME;
