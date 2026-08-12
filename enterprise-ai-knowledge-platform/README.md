# Enterprise AI Knowledge Platform

A production-ready Enterprise AI Knowledge Platform implemented using native Snowflake Cortex AI capabilities. Enables business users to interact with enterprise knowledge stored across multiple document types and departments through an intelligent AI Agent.

**Zero external AI frameworks.** No LangChain, no external vector databases, no third-party orchestration. 100% Snowflake-native AI.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                             │
│  Streamlit in Snowflake │ REST API (SPCS) │ External Apps        │
├─────────────────────────────────────────────────────────────────┤
│                    AGENT LAYER                                    │
│  Cortex Agent │ Tool Calling │ Conversation Memory │ Guardrails  │
├─────────────────────────────────────────────────────────────────┤
│                    KNOWLEDGE LAYER                                │
│  Cortex Search │ VECTOR(1024) │ Semantic Chunking │ Catalog      │
├─────────────────────────────────────────────────────────────────┤
│                    INTELLIGENCE LAYER                             │
│  AI_PARSE_DOCUMENT │ OCR │ Classification │ Metadata Extraction  │
├─────────────────────────────────────────────────────────────────┤
│                    STORAGE & GOVERNANCE                           │
│  Internal Stages │ Row Access Policies │ Masking │ Tags │ Audit  │
└─────────────────────────────────────────────────────────────────┘
```

## Key Capabilities

| Capability | Snowflake Feature |
|-----------|-------------------|
| Document Parsing | AI_PARSE_DOCUMENT |
| OCR | AI_PARSE_DOCUMENT (OCR mode) |
| Classification | CORTEX COMPLETE (structured output) |
| Embeddings | EMBED_TEXT_1024 (snowflake-arctic-embed-l-v2.0) |
| Vector Storage | VECTOR(FLOAT, 1024) |
| Semantic Search | Cortex Search Service (hybrid) |
| AI Agent | CREATE CORTEX AGENT |
| Orchestration | Tasks + Streams + Dynamic Tables |
| Access Control | Row Access Policies + RBAC |
| Data Masking | Masking Policies (PII) |
| Cost Tracking | Dynamic Tables (hourly aggregation) |

## Supported Document Types

PDF, DOCX, XLSX, PPTX, CSV, JSON, HTML, TXT, PNG, JPG

## Business Departments

Finance, Treasury, Procurement, Risk, Compliance, Audit, Human Resources, Legal, Operations

## Project Structure

```
enterprise-ai-knowledge-platform/
├── src/                          # Python source code
│   ├── shared/                   # Config, models, exceptions, session
│   ├── document_intelligence/    # Parsing, classification, extraction
│   ├── knowledge_repository/     # Chunking, embeddings, search, catalog
│   ├── agent_runtime/            # Agent service, tools, memory, planning
│   ├── guardrails/               # Groundedness, PII, injection, toxicity
│   ├── governance/               # Audit logging
│   ├── observability/            # Metrics tracking
│   └── api/                      # FastAPI REST service (for SPCS)
├── sql/                          # All Snowflake DDL (ordered deployment)
│   ├── schemas/                  # Database + schema creation
│   ├── tables/                   # All table definitions (6 files)
│   ├── roles/                    # RBAC hierarchy + privilege grants
│   ├── stages/                   # Per-department internal stages
│   ├── policies/                 # Row access, masking, tags
│   ├── tasks/                    # Ingestion pipeline tasks
│   ├── dynamic_tables/           # Chunk + catalog auto-refresh
│   ├── udfs/                     # Chunking UDF
│   ├── cortex_search/            # Search service definition
│   ├── agents/                   # Cortex Agent + tool functions
│   └── procedures/               # SPCS service spec
├── streamlit/                    # Streamlit in Snowflake UI (6 pages)
├── config/                       # YAML configuration
│   ├── platform.yaml             # Departments, file types, schemas
│   ├── environments/             # dev.yaml, prod.yaml
│   ├── prompts/                  # Versioned prompt templates
│   └── guardrails/               # Validator rules
├── scripts/                      # Deployment + data generation
├── tests/                        # Unit, integration, E2E tests
├── data/sample_documents/        # 10 realistic documents (9 departments)
├── docs/                         # Architecture, deployment, runbooks
├── Dockerfile                    # SPCS container image
├── pyproject.toml                # Python dependencies + tooling
└── COCO.md                       # Project conventions
```

## Quick Start

### Prerequisites

- Snowflake account with Cortex AI enabled
- Python 3.10+
- `ACCOUNTADMIN` or `SYSADMIN` role for initial deployment

### 1. Deploy Snowflake Objects

```bash
# Review execution plan
python scripts/deploy.py --account YOUR_ORG-YOUR_ACCOUNT --user YOUR_USER --dry-run

# Deploy all SQL objects
python scripts/deploy.py --account YOUR_ORG-YOUR_ACCOUNT --user YOUR_USER --authenticator externalbrowser
```

### 2. Generate and Upload Sample Data

```bash
python scripts/generate_sample_data.py
python scripts/upload_samples.py
```

### 3. Enable Pipeline Tasks

```sql
ALTER TASK RAW.DOCUMENT_INGESTION_TASK RESUME;
ALTER TASK RAW.DOCUMENT_RETRY_TASK RESUME;
```

### 4. Deploy Streamlit App

Upload the `streamlit/` directory to Snowflake as a Streamlit in Snowflake application.

### 5. Run Tests

```bash
pip install -e ".[dev]"
pytest tests/unit -m unit          # No Snowflake needed
pytest tests/integration -m integration  # Requires connection
pytest tests/e2e -m e2e            # Full pipeline
```

## Configuration

All behavior is YAML-driven:

- **`config/platform.yaml`** — Departments, file types, schemas
- **`config/environments/dev.yaml`** — Dev settings (XSMALL warehouses)
- **`config/environments/prod.yaml`** — Prod settings (scaled warehouses)
- **`config/prompts/templates.yaml`** — LLM prompt templates
- **`config/guardrails/validators.yaml`** — PII patterns, thresholds

Environment variables (via `.env`):
```
SNOWFLAKE_ACCOUNT=your_org-your_account
SNOWFLAKE_USER=your_user
SNOWFLAKE_PRIVATE_KEY_PATH=~/.ssh/snowflake_rsa_key.p8
ENVIRONMENT=dev
```

## Security Model

- **12 roles** in hierarchy: 9 department + User + Service + Admin
- **Row Access Policies** enforce department-level document isolation
- **Masking Policies** protect PII (SSN, credit cards) from non-admin roles
- **Object Tags** classify sensitivity, department, PII presence, retention
- **Guardrails** block prompt injection and mask PII in AI responses

## Observability

- Token usage tracking (per model, per operation)
- Search quality diagnostics (latency, relevance scores)
- Agent execution traces (step-by-step reasoning)
- Cost aggregation via Dynamic Table (hourly rollup)
- Guardrail violation logging

## Technology Stack

| Layer | Technology |
|-------|-----------|
| AI Models | Claude 3.5 Sonnet/Haiku (via Cortex) |
| Embeddings | snowflake-arctic-embed-l-v2.0 |
| Search | Cortex Search Service |
| Agent | Cortex Agent (CREATE AGENT) |
| Storage | Snowflake Internal Stages |
| Vectors | VECTOR(FLOAT, 1024) |
| Orchestration | Tasks, Streams, Dynamic Tables |
| UI | Streamlit in Snowflake |
| API | FastAPI on SPCS |
| IaC | Terraform (Snowflake Provider) |
| Testing | pytest (unit/integration/e2e) |
| Linting | Ruff, mypy |
