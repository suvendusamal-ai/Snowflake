-- One-time Snowflake setup script for CSV ingestion
-- Update DATABASE and SCHEMA names if your environment uses different values.

CREATE DATABASE IF NOT EXISTS DEMODB;
USE DATABASE DEMODB;

CREATE SCHEMA IF NOT EXISTS ATLAS;
USE SCHEMA ATLAS;

CREATE FILE FORMAT IF NOT EXISTS csv_file_format
  TYPE = CSV
  FIELD_DELIMITER = ','
  SKIP_HEADER = 1
  FIELD_OPTIONALLY_ENCLOSED_BY = '"'
  TRIM_SPACE = TRUE
  ERROR_ON_COLUMN_COUNT_MISMATCH = FALSE
  EMPTY_FIELD_AS_NULL = TRUE;

CREATE STAGE IF NOT EXISTS csv_ingest_stage
  FILE_FORMAT = (FORMAT_NAME = csv_file_format);

-- Run this script once before starting the FastAPI service.
-- The application assumes the stage and file format already exist and does not recreate them each request.
