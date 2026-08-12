# Enterprise AI Knowledge Platform — Architecture Diagrams

## 1. System Context Diagram

```mermaid
C4Context
    title System Context - Enterprise AI Knowledge Platform

    Person(user, "Business User", "Finance, HR, Legal, etc.")
    Person(admin, "Platform Admin", "Manages platform, monitors health")
    Person(dev, "Developer", "Integrates via REST API")

    System(platform, "Enterprise AI Knowledge Platform", "Snowflake Cortex AI-powered knowledge management")

    System_Ext(docs, "Enterprise Documents", "PDF, DOCX, XLSX, PPTX, CSV, HTML, Images")
    System_Ext(react, "External Applications", "React, Angular, Mobile")

    Rel(user, platform, "Asks questions, uploads docs", "Streamlit UI")
    Rel(admin, platform, "Monitors, configures", "Streamlit Admin")
    Rel(dev, platform, "Integrates", "REST API")
    Rel(docs, platform, "Ingested into", "Internal Stages")
    Rel(platform, react, "Serves API", "HTTPS/JSON")
```

## 2. High-Level Architecture

```mermaid
graph TB
    subgraph "USER INTERFACES"
        SIS["Streamlit in Snowflake<br/>(6 pages)"]
        API["REST API<br/>(FastAPI on SPCS)"]
        EXT["External Apps<br/>(React/Angular/Mobile)"]
    end

    subgraph "AI AGENT LAYER"
        AGENT["Cortex Agent<br/>ENTERPRISE_KNOWLEDGE_AGENT"]
        TOOLS["Tool Functions<br/>5 SQL tools"]
        GUARD_IN["Input Guardrails<br/>Injection + PII"]
        GUARD_OUT["Output Guardrails<br/>Groundedness + PII Mask + Toxicity"]
        MEMORY["Conversation Memory<br/>Sliding window (20 msgs)"]
    end

    subgraph "KNOWLEDGE LAYER"
        CS["Cortex Search Service<br/>ENTERPRISE_KNOWLEDGE_SEARCH<br/>(hybrid: semantic + BM25)"]
        VEC["Vector Store<br/>VECTOR(FLOAT, 1024)<br/>snowflake-arctic-embed-l-v2.0"]
        CAT["Knowledge Catalog<br/>Document-level summaries"]
    end

    subgraph "DOCUMENT INTELLIGENCE LAYER"
        PARSE["AI_PARSE_DOCUMENT<br/>(PDF, DOCX, PPTX, HTML)"]
        OCR["OCR<br/>(PNG, JPG)"]
        CLASS["AI Classifier<br/>CORTEX COMPLETE<br/>(dept, type, sensitivity)"]
        EXTRACT["Metadata Extractor<br/>CORTEX COMPLETE<br/>(dept-specific fields)"]
        CHUNK["Semantic Chunker<br/>Python UDF<br/>(1500 chars, 200 overlap)"]
        EMBED["EMBED_TEXT_1024<br/>snowflake-arctic-embed-l-v2.0"]
    end

    subgraph "ORCHESTRATION LAYER"
        STREAM["Stream<br/>DOCUMENT_REGISTRY_STREAM<br/>(append-only CDC)"]
        TASK1["Task: INGESTION<br/>(every 1 min)"]
        TASK2["Task: RETRY<br/>(every 15 min, max 3)"]
        DT1["Dynamic Table<br/>DOCUMENT_CHUNKS_DT<br/>(5 min lag)"]
        DT2["Dynamic Table<br/>KNOWLEDGE_CATALOG_DT<br/>(10 min lag)"]
    end

    subgraph "STORAGE LAYER"
        STAGES["Internal Stages (x9)<br/>FINANCE_DOCS, TREASURY_DOCS, ..."]
        RAW["RAW Schema<br/>DOCUMENT_REGISTRY"]
        PROC["PROCESSED Schema<br/>PARSED_DOCUMENTS<br/>CLASSIFICATIONS<br/>METADATA"]
        KNOW["KNOWLEDGE Schema<br/>DOCUMENT_CHUNKS<br/>KNOWLEDGE_CATALOG"]
    end

    subgraph "GOVERNANCE LAYER"
        RBAC["RBAC<br/>12 roles, hierarchy"]
        RAP["Row Access Policy<br/>Department isolation"]
        MASK["Masking Policies<br/>PII: SSN, CC, Email"]
        TAGS["Object Tags<br/>Dept, Sensitivity, PII"]
        AUDIT["Audit Logs<br/>Access + AI Governance"]
    end

    %% User flows
    SIS --> GUARD_IN
    API --> GUARD_IN
    EXT --> API
    GUARD_IN --> AGENT
    AGENT --> TOOLS
    AGENT --> MEMORY
    TOOLS --> CS
    TOOLS --> CAT
    AGENT --> GUARD_OUT
    GUARD_OUT --> SIS

    %% Search flow
    CS --> VEC
    VEC --> KNOW

    %% Ingestion flow
    STAGES --> RAW
    RAW --> STREAM
    STREAM --> TASK1
    TASK1 --> PARSE
    TASK1 --> OCR
    TASK1 --> CLASS
    PARSE --> PROC
    CLASS --> PROC
    EXTRACT --> PROC
    PROC --> DT1
    DT1 --> CHUNK
    CHUNK --> EMBED
    EMBED --> KNOW
    KNOW --> CS
    DT2 --> CAT

    TASK2 -.->|retries failed| TASK1

    %% Governance
    RAP -.-> KNOW
    MASK -.-> PROC
    AUDIT -.-> AGENT
```

## 3. End-to-End Process Flow — Document Ingestion

```mermaid
sequenceDiagram
    autonumber
    participant U as User/System
    participant ST as Streamlit UI
    participant STG as Internal Stage<br/>(per department)
    participant REG as DOCUMENT_REGISTRY<br/>(RAW)
    participant STR as Stream<br/>(CDC)
    participant TSK as Ingestion Task<br/>(1 min schedule)
    participant AIP as AI_PARSE_DOCUMENT
    participant CLS as CORTEX COMPLETE<br/>(Classifier)
    participant EXT as CORTEX COMPLETE<br/>(Extractor)
    participant CHK as CHUNK_DOCUMENT_UDF
    participant EMB as EMBED_TEXT_1024
    participant CHUNKS as DOCUMENT_CHUNKS<br/>(KNOWLEDGE)
    participant CSS as Cortex Search Service

    U->>ST: Upload document (PDF/DOCX/etc.)
    ST->>STG: PUT file to department stage
    ST->>REG: INSERT (file_name, dept, stage_path, status=PENDING)

    Note over STR: Stream detects new row (append-only)

    STR->>TSK: SYSTEM$STREAM_HAS_DATA = TRUE
    TSK->>REG: UPDATE status = 'PARSING'
    TSK->>AIP: AI_PARSE_DOCUMENT(BUILD_SCOPED_FILE_URL(...), 'LAYOUT')
    AIP-->>TSK: Structured text + page count

    TSK->>REG: UPDATE status = 'CLASSIFYING'
    TSK->>CLS: CORTEX.COMPLETE('classify this document...')
    CLS-->>TSK: {department, document_type, sensitivity, topics}

    TSK->>EXT: CORTEX.COMPLETE('extract metadata fields...')
    EXT-->>TSK: {key: value} pairs (dept-specific)

    TSK->>REG: UPDATE status = 'COMPLETED'

    Note over CHK: Dynamic Table (5 min lag) triggers

    CHK->>CHK: Split text into semantic chunks<br/>(1500 chars, 200 overlap)
    CHK->>EMB: EMBED_TEXT_1024(chunk_text)
    EMB-->>CHUNKS: Store chunk + VECTOR(FLOAT, 1024)

    Note over CSS: Cortex Search Service (5 min lag) auto-indexes

    CSS->>CSS: Update hybrid index<br/>(semantic + keyword)

    Note over U: Document now searchable!
```

## 4. End-to-End Process Flow — Query & Response

```mermaid
sequenceDiagram
    autonumber
    participant U as Business User
    participant ST as Streamlit Chat
    participant GI as Input Guardrails
    participant AG as Cortex Agent<br/>ENTERPRISE_KNOWLEDGE_AGENT
    participant CS as Cortex Search Service<br/>(Hybrid: Vector + BM25)
    participant TL as Tool Functions
    participant MEM as Conversation Memory
    participant GO as Output Guardrails
    participant AUD as Audit Logger

    U->>ST: "What is our Q4 revenue by segment?"
    ST->>MEM: Retrieve conversation history (last 20 msgs)
    ST->>GI: Validate input

    alt Injection Detected
        GI-->>ST: BLOCKED (score ≥ 0.8)
        ST-->>U: "Query blocked by safety filters"
    end

    GI-->>ST: PASSED
    ST->>AG: Invoke agent with query + history + dept context

    Note over AG: Agent plans tool usage

    AG->>CS: SEARCH_KNOWLEDGE("Q4 revenue segment")
    CS-->>AG: Top 10 chunks with scores

    AG->>TL: GET_DOCUMENT_DETAILS(doc_id)
    TL-->>AG: Document metadata + summary

    Note over AG: Agent synthesizes response with citations

    AG-->>ST: Response + citations + token count

    ST->>GO: Validate output

    par Groundedness Check
        GO->>GO: Verify claims against search context
    and PII Detection
        GO->>GO: Regex scan for SSN/CC/email
    and Toxicity Check
        GO->>GO: Score for harmful content
    end

    alt PII Found in Response
        GO->>GO: Mask PII (***-**-1234)
    end

    GO-->>ST: Modified response (if PII masked)

    ST->>MEM: Store user message + assistant response
    ST->>AUD: Log AI decision + guardrail results

    ST-->>U: "Q4 2024 revenue was $2.87B...<br/>[Source: Q4_2024_Financial_Report.txt]"
```

## 5. Security Architecture

```mermaid
graph LR
    subgraph "Authentication"
        JWT["JWT Token<br/>(Snowflake OAuth)"]
        APIKEY["API Key<br/>(service-to-service)"]
        SIS_AUTH["Streamlit Auth<br/>(built-in)"]
    end

    subgraph "Authorization (RBAC)"
        ADMIN["CORTEX_AI_ADMIN<br/>Full access"]
        SVC["CORTEX_AI_SERVICE<br/>Pipeline execution"]
        USR["CORTEX_AI_USER<br/>Read + search"]
        DEPT["CORTEX_AI_{DEPT}<br/>Department scoped"]
    end

    subgraph "Data Protection"
        RAP["Row Access Policy<br/>DEPARTMENT column filter"]
        MASK_SSN["Masking: SSN<br/>***-**-1234"]
        MASK_CC["Masking: Credit Card<br/>****-****-****-1234"]
        MASK_EMAIL["Masking: Email<br/>j***@domain.com"]
    end

    subgraph "AI Safety"
        INJ["Injection Detection<br/>15 regex + LLM scoring"]
        GND["Groundedness<br/>Claim verification"]
        TOX["Toxicity<br/>4 harm categories"]
        PII_OUT["PII Masking<br/>Response sanitization"]
    end

    JWT --> ADMIN
    JWT --> USR
    APIKEY --> SVC
    SIS_AUTH --> USR

    ADMIN --> RAP
    USR --> RAP
    DEPT --> RAP

    RAP --> MASK_SSN
    RAP --> MASK_CC
    RAP --> MASK_EMAIL

    INJ --> GND
    GND --> TOX
    TOX --> PII_OUT
```

## 6. Data Model (Entity Relationship)

```mermaid
erDiagram
    DOCUMENT_REGISTRY ||--o{ PARSED_DOCUMENTS : "1:1 parsed"
    DOCUMENT_REGISTRY ||--o{ DOCUMENT_CLASSIFICATIONS : "1:1 classified"
    DOCUMENT_REGISTRY ||--o{ DOCUMENT_METADATA : "1:N metadata"
    DOCUMENT_REGISTRY ||--o{ DOCUMENT_CHUNKS : "1:N chunks"
    DOCUMENT_CHUNKS ||--|| KNOWLEDGE_CATALOG : "aggregates to"
    CONVERSATIONS ||--o{ CONVERSATION_MESSAGES : "contains"
    CONVERSATIONS ||--o{ AGENT_TRACES : "traced by"

    DOCUMENT_REGISTRY {
        varchar DOCUMENT_ID PK
        varchar FILE_NAME
        varchar FILE_TYPE
        number FILE_SIZE_BYTES
        varchar DEPARTMENT
        varchar STAGE_PATH
        varchar PROCESSING_STATUS
        timestamp UPLOAD_TIMESTAMP
    }

    PARSED_DOCUMENTS {
        varchar PARSE_ID PK
        varchar DOCUMENT_ID FK
        varchar PARSED_CONTENT
        number WORD_COUNT
        varchar PARSE_MODEL
    }

    DOCUMENT_CLASSIFICATIONS {
        varchar CLASSIFICATION_ID PK
        varchar DOCUMENT_ID FK
        varchar DEPARTMENT
        varchar DOCUMENT_TYPE
        varchar SENSITIVITY_LEVEL
        array TOPICS
        float CONFIDENCE_SCORE
    }

    DOCUMENT_CHUNKS {
        varchar CHUNK_ID PK
        varchar DOCUMENT_ID FK
        number CHUNK_INDEX
        varchar CHUNK_TEXT
        varchar DEPARTMENT
        vector EMBEDDING "VECTOR(FLOAT 1024)"
    }

    KNOWLEDGE_CATALOG {
        varchar CATALOG_ID PK
        varchar DOCUMENT_ID FK
        varchar TITLE
        varchar DEPARTMENT
        number CHUNK_COUNT
        number TOTAL_TOKENS
    }

    CONVERSATIONS {
        varchar CONVERSATION_ID PK
        varchar USER_ID
        varchar DEPARTMENT
        varchar TITLE
        number MESSAGE_COUNT
        varchar STATUS
    }

    CONVERSATION_MESSAGES {
        varchar MESSAGE_ID PK
        varchar CONVERSATION_ID FK
        varchar ROLE
        varchar CONTENT
        array CITATIONS
        number TOKEN_COUNT
    }
```

## 7. Deployment Architecture

```mermaid
graph TB
    subgraph "Snowflake Account: EKDYHXP-GA44877"
        subgraph "Database: CORTEX_AI_PLATFORM"
            RAW_S["RAW Schema<br/>9 Stages + Registry + Stream"]
            PROC_S["PROCESSED Schema<br/>4 Tables"]
            KNOW_S["KNOWLEDGE Schema<br/>4 Tables + Search Service + UDF"]
            AGENT_S["AGENT Schema<br/>5 Tables + Agent + 5 Tool Functions"]
            GOV_S["GOVERNANCE Schema<br/>4 Tables + Policies + Tags"]
            OBS_S["OBSERVABILITY Schema<br/>3 Tables + Cost DT"]
        end

        subgraph "Warehouses"
            WH1["CORTEX_AI_INGESTION_WH<br/>Parsing, embedding, tasks"]
            WH2["CORTEX_AI_SEARCH_WH<br/>Search, agent execution"]
            WH3["CORTEX_AI_ANALYTICS_WH<br/>Observability, admin"]
            WH4["CORTEX_AI_STREAMLIT_WH<br/>UI serving"]
        end

        subgraph "Compute Services"
            TASK_SVC["Tasks (2)<br/>Ingestion + Retry"]
            DT_SVC["Dynamic Tables (3)<br/>Chunks + Catalog + Cost"]
            CSS_SVC["Cortex Search<br/>ENTERPRISE_KNOWLEDGE_SEARCH"]
            AGENT_SVC["Cortex Agent<br/>ENTERPRISE_KNOWLEDGE_AGENT"]
        end

        subgraph "SPCS (Optional)"
            POOL["Compute Pool<br/>CPU_X64_XS (1-3 nodes)"]
            CONTAINER["API Container<br/>FastAPI + uvicorn"]
        end

        subgraph "Streamlit in Snowflake"
            SIS_APP["Knowledge Platform App<br/>6 pages"]
        end
    end

    SIS_APP --> WH4
    SIS_APP --> AGENT_SVC
    CONTAINER --> WH2
    TASK_SVC --> WH1
    DT_SVC --> WH1
    CSS_SVC --> WH2
    AGENT_SVC --> CSS_SVC
```

## 8. Component Interaction Map

```mermaid
flowchart LR
    subgraph "Ingestion Path"
        A[Upload] --> B[Stage]
        B --> C[Registry]
        C --> D[Stream]
        D --> E[Task]
        E --> F[Parse]
        F --> G[Classify]
        G --> H[Extract Meta]
    end

    subgraph "Knowledge Path"
        H --> I[Dynamic Table]
        I --> J[Chunk UDF]
        J --> K[EMBED_TEXT]
        K --> L[VECTOR Store]
        L --> M[Cortex Search]
    end

    subgraph "Query Path"
        N[User Query] --> O[Guardrails In]
        O --> P[Agent]
        P --> Q[Search Tool]
        Q --> M
        M --> R[Context]
        R --> P
        P --> S[Response]
        S --> T[Guardrails Out]
        T --> U[User]
    end

    style A fill:#e1f5fe
    style N fill:#e8f5e9
    style M fill:#fff3e0
```
