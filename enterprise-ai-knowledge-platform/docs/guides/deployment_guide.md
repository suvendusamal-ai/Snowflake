# Deployment Guide

## Prerequisites

- Snowflake account with **Cortex AI** enabled (arctic-embed, Claude models)
- Python 3.10+ installed locally
- User with `ACCOUNTADMIN` or `SYSADMIN` role for initial setup
- Network access to Snowflake account

## Step 1: Environment Setup

```bash
# Clone the repository
cd enterprise-ai-knowledge-platform

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
# Edit .env with your Snowflake credentials
```

## Step 2: Configure Environment

Edit `.env`:
```
SNOWFLAKE_ACCOUNT=YOUR_ORG-YOUR_ACCOUNT
SNOWFLAKE_USER=YOUR_USER
SNOWFLAKE_PRIVATE_KEY_PATH=~/.ssh/snowflake_rsa_key.p8
SNOWFLAKE_ROLE=SYSADMIN
ENVIRONMENT=dev
```

## Step 3: Deploy Snowflake Objects

The deployment script executes SQL files in dependency order:

```bash
# Preview what will be deployed
python scripts/deploy.py \
    --account YOUR_ORG-YOUR_ACCOUNT \
    --user YOUR_USER \
    --dry-run

# Deploy all objects
python scripts/deploy.py \
    --account YOUR_ORG-YOUR_ACCOUNT \
    --user YOUR_USER \
    --authenticator externalbrowser
```

### SQL Execution Order

| Step | File | Creates |
|------|------|---------|
| 00 | schemas/001_create_database.sql | CORTEX_AI_PLATFORM database |
| 01 | schemas/002_create_schemas.sql | 6 schemas |
| 02 | roles/001_create_roles.sql | 12 roles + hierarchy |
| 03 | roles/002_grant_privileges.sql | Privilege grants |
| 04 | stages/001_create_stages.sql | 9 department stages + temp |
| 05 | tables/001_raw_tables.sql | DOCUMENT_REGISTRY + Stream |
| 06 | tables/002_processed_tables.sql | Parsed, classifications, metadata |
| 07 | tables/003_knowledge_tables.sql | Chunks (VECTOR), catalog, lineage |
| 08 | tables/004_agent_tables.sql | Conversations, tools, traces |
| 09 | tables/005_governance_tables.sql | Audit logs, lineage seed |
| 10 | tables/006_observability_tables.sql | Token, search, latency metrics |
| 11 | policies/001_row_access_policies.sql | Department isolation |
| 12 | policies/002_masking_policies.sql | PII masking |
| 13 | policies/003_tags.sql | 5 governance tags |
| 14 | dynamic_tables/001_document_chunks.sql | Chunk + catalog DTs |
| 15 | tasks/001_ingestion_pipeline.sql | Processing procedure + tasks |
| 16 | udfs/001_chunking_udf.sql | CHUNK_DOCUMENT_UDF |
| 17 | cortex_search/001_create_service.sql | ENTERPRISE_KNOWLEDGE_SEARCH |
| 18 | agents/001_create_agent.sql | Tool functions + Cortex Agent |
| 19 | procedures/001_spcs_service.sql | API container service |

### Resume from a specific step

If deployment fails mid-way:
```bash
python scripts/deploy.py --account ... --user ... --from-step 14
```

## Step 4: Enable Pipeline

```sql
-- Connect as CORTEX_AI_ADMIN
USE ROLE CORTEX_AI_ADMIN;
USE WAREHOUSE CORTEX_AI_INGESTION_WH;

-- Start the ingestion pipeline
ALTER TASK RAW.DOCUMENT_INGESTION_TASK RESUME;
ALTER TASK RAW.DOCUMENT_RETRY_TASK RESUME;

-- Verify tasks are running
SHOW TASKS IN SCHEMA RAW;
```

## Step 5: Load Sample Data

```bash
# Generate sample documents
python scripts/generate_sample_data.py

# Upload to Snowflake stages
python scripts/upload_samples.py
```

Verify processing:
```sql
SELECT PROCESSING_STATUS, COUNT(*)
FROM RAW.DOCUMENT_REGISTRY
GROUP BY PROCESSING_STATUS;
-- Expected: COMPLETED = 10 (after pipeline processes them)
```

## Step 6: Deploy Streamlit Application

### Option A: Streamlit in Snowflake (Recommended)

1. Navigate to Snowsight → Streamlit
2. Create new Streamlit app
3. Set warehouse: `CORTEX_AI_STREAMLIT_WH`
4. Upload `streamlit/app.py` and `streamlit/pages/` directory
5. Set app role: `CORTEX_AI_USER`

### Option B: Local Development

```bash
cd streamlit
streamlit run app.py
```

## Step 7: Deploy REST API (Optional - SPCS)

Only required for external application integration.

```bash
# Build container image
docker build -t knowledge-api:latest .

# Tag for Snowflake registry
docker tag knowledge-api:latest \
    YOUR_ORG-YOUR_ACCOUNT.registry.snowflakecomputing.com/cortex_ai_platform/raw/api_images/knowledge-api:latest

# Push to Snowflake
docker push YOUR_ORG-YOUR_ACCOUNT.registry.snowflakecomputing.com/cortex_ai_platform/raw/api_images/knowledge-api:latest

# Deploy SPCS service (already in SQL step 19)
-- Service will start automatically after image push
```

## Step 8: Verify Deployment

```bash
# Run integration tests
pytest tests/integration -m integration -v

# Run E2E test
pytest tests/e2e -m e2e -v
```

### Manual Verification

```sql
-- Test search
SELECT * FROM TABLE(AGENT.SEARCH_KNOWLEDGE('quarterly revenue', NULL, 5));

-- Test agent
SELECT SNOWFLAKE.CORTEX.COMPLETE(
    'claude-3-5-sonnet',
    'What are the key financial metrics from Q4 2024?'
);

-- Check pipeline health
SELECT PROCESSING_STATUS, COUNT(*), MAX(LAST_PROCESSED_AT)
FROM RAW.DOCUMENT_REGISTRY
GROUP BY PROCESSING_STATUS;
```

## Post-Deployment

### Assign Users to Department Roles

```sql
-- Grant finance access to a user
GRANT ROLE CORTEX_AI_FINANCE TO USER finance_analyst;
GRANT ROLE CORTEX_AI_USER TO USER finance_analyst;
```

### Set Up Monitoring

```sql
-- Create alert for failed documents
CREATE ALERT OBSERVABILITY.FAILED_DOCUMENTS_ALERT
    WAREHOUSE = CORTEX_AI_ANALYTICS_WH
    SCHEDULE = '15 MINUTE'
    IF (EXISTS (
        SELECT 1 FROM RAW.DOCUMENT_REGISTRY
        WHERE PROCESSING_STATUS = 'FAILED'
          AND RETRY_COUNT >= 3
          AND LAST_PROCESSED_AT > DATEADD('MINUTE', -15, CURRENT_TIMESTAMP())
    ))
    THEN
        CALL SYSTEM$SEND_EMAIL(...);
```

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Task not running | Suspended | `ALTER TASK ... RESUME` |
| EMBED_TEXT fails | Model not available in region | Check Cortex availability |
| Search returns 0 results | No embeddings yet | Wait for DT refresh (5 min lag) |
| Row access denies query | Wrong role | Grant department role to user |
| Dynamic Table stale | Warehouse suspended | Resume warehouse |
