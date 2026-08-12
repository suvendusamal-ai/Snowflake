# Architecture Guide

## Overview

The Enterprise AI Knowledge Platform follows a layered architecture with clear separation of concerns. Each layer communicates only with its adjacent layers, and all data flows through Snowflake-native services.

## Logical Architecture

```mermaid
graph TB
    subgraph "User Layer"
        SIS[Streamlit in Snowflake]
        API[REST API - SPCS]
        EXT[External Apps]
    end

    subgraph "Agent Layer"
        AG[Cortex Agent]
        TL[Tool Registry]
        MEM[Conversation Memory]
        GR[Guardrails Engine]
    end

    subgraph "Knowledge Layer"
        CS[Cortex Search Service]
        EMB[EMBED_TEXT_1024]
        CHK[Semantic Chunker UDF]
        CAT[Knowledge Catalog]
    end

    subgraph "Intelligence Layer"
        PARSE[AI_PARSE_DOCUMENT]
        CLASS[Classifier - CORTEX COMPLETE]
        META[Metadata Extractor]
    end

    subgraph "Orchestration Layer"
        STREAM[Document Registry Stream]
        TASK[Ingestion Task - 1 min]
        DT[Dynamic Tables - 5/10 min lag]
        RETRY[Retry Task - 15 min]
    end

    subgraph "Storage Layer"
        STG[Internal Stages x9]
        RAW[RAW Schema]
        PROC[PROCESSED Schema]
        KNOW[KNOWLEDGE Schema]
        AGNT[AGENT Schema]
        GOV[GOVERNANCE Schema]
        OBS[OBSERVABILITY Schema]
    end

    SIS --> AG
    API --> AG
    AG --> CS
    AG --> TL
    AG --> MEM
    AG --> GR
    CS --> KNOW
    EMB --> KNOW
    CHK --> PROC
    PARSE --> PROC
    CLASS --> PROC
    META --> PROC
    STREAM --> TASK
    TASK --> PARSE
    TASK --> CLASS
    DT --> CHK
    DT --> EMB
    STG --> RAW
end
```

## Physical Architecture (Snowflake Objects)

### Database: CORTEX_AI_PLATFORM

| Schema | Purpose | Key Objects |
|--------|---------|------------|
| RAW | Ingestion | 9 stages, DOCUMENT_REGISTRY, Stream |
| PROCESSED | Parsed content | PARSED_DOCUMENTS, CLASSIFICATIONS, METADATA, LOG |
| KNOWLEDGE | Search-ready | DOCUMENT_CHUNKS (VECTOR), CATALOG, Cortex Search |
| AGENT | Runtime | CONVERSATIONS, MESSAGES, TOOL_REGISTRY, TRACES, Agent |
| GOVERNANCE | Policies | AUDIT_LOG, AI_GOV_LOG, LINEAGE, Row Access Policy |
| OBSERVABILITY | Metrics | TOKEN_USAGE, SEARCH_DIAGNOSTICS, LATENCY, Cost DT |

### Warehouses

| Warehouse | Workload | Size (Dev/Prod) |
|-----------|----------|-----------------|
| CORTEX_AI_INGESTION_WH | Parsing, embedding, tasks | XS / M |
| CORTEX_AI_SEARCH_WH | Search, agent execution | XS / S |
| CORTEX_AI_ANALYTICS_WH | Observability, admin | XS / S |
| CORTEX_AI_STREAMLIT_WH | Streamlit app | XS / S |

### Role Hierarchy

```
SYSADMIN
└── CORTEX_AI_ADMIN
    └── CORTEX_AI_SERVICE
        └── CORTEX_AI_USER
            ├── CORTEX_AI_FINANCE
            ├── CORTEX_AI_TREASURY
            ├── CORTEX_AI_PROCUREMENT
            ├── CORTEX_AI_RISK
            ├── CORTEX_AI_COMPLIANCE
            ├── CORTEX_AI_AUDIT
            ├── CORTEX_AI_HR
            ├── CORTEX_AI_LEGAL
            └── CORTEX_AI_OPERATIONS
```

## Data Flow

### Ingestion Pipeline

```
Document Upload → Internal Stage → DOCUMENT_REGISTRY (CHANGE_TRACKING)
    │
    ▼ [Stream + Task - 1 min]
AI_PARSE_DOCUMENT → PARSED_DOCUMENTS
    │
    ▼ [CORTEX COMPLETE]
Classification → DOCUMENT_CLASSIFICATIONS
    │
    ▼ [Dynamic Table - 5 min]
CHUNK_DOCUMENT_UDF → EMBED_TEXT_1024 → DOCUMENT_CHUNKS (VECTOR)
    │
    ▼ [Cortex Search - 5 min lag]
ENTERPRISE_KNOWLEDGE_SEARCH (hybrid index)
```

### Query Flow

```
User Question → Guardrails (input) → Agent
    │
    Agent → Tool Selection → Cortex Search
    │                     → GET_CATALOG
    │                     → GET_DOCUMENT_DETAILS
    │
    Agent → Response Generation → Guardrails (output)
    │                                        │
    │                               ├── Groundedness check
    │                               ├── PII masking
    │                               └── Toxicity check
    │
    └── Final Response (with citations) → User
```

## Design Decisions

### Why Cortex Search over raw Vector Search?

| Criteria | Cortex Search | Raw VECTOR |
|----------|--------------|-----------|
| Index management | Automatic | Manual |
| Hybrid search | Built-in (semantic + keyword) | Semantic only |
| Filtering | Native filter syntax | WHERE clause |
| Freshness | TARGET_LAG auto-refresh | Manual re-embed |
| Maintenance | Zero-ops | Index monitoring |

### Why Dynamic Tables over Tasks for chunk pipeline?

- **Declarative**: Define the transformation, not the execution schedule
- **Incremental**: Only processes new/changed source rows
- **Composable**: DT chains (parse → chunk → catalog) with independent lag
- **Observable**: Built-in refresh monitoring via INFORMATION_SCHEMA

### Why single Cortex Search Service vs per-department?

- **Unified index**: One search call, filters enforce department access
- **Row Access Policy**: Same SQL-level enforcement regardless of search path
- **Simpler management**: One service to monitor, one TARGET_LAG to tune
- **Cross-department queries**: Admin/Service roles can search across all

## Scalability Considerations

| Dimension | Strategy |
|-----------|----------|
| Document volume | Horizontal: Dynamic Tables scale with warehouse size |
| Concurrent users | SPCS auto-scale (1-3 instances), Streamlit per-user sessions |
| Search performance | Cortex Search managed scaling, add per-dept services if needed |
| Embedding throughput | Warehouse scaling (XS→M→L) for batch embedding |
| Cost control | Auto-suspend (60s), resource monitors, hourly cost DT |
