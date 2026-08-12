-- ============================================================================
-- Enterprise AI Knowledge Platform
-- Schema Creation
-- ============================================================================

USE ROLE SYSADMIN;
USE DATABASE CORTEX_AI_PLATFORM;

-- RAW: Document ingestion, stages, raw metadata
CREATE SCHEMA IF NOT EXISTS RAW
    COMMENT = 'Raw document ingestion layer - stages, registry, unprocessed content';

-- PROCESSED: Parsed documents, classifications, extracted metadata
CREATE SCHEMA IF NOT EXISTS PROCESSED
    COMMENT = 'Processed document layer - parsed content, classifications, metadata';

-- KNOWLEDGE: Chunks, embeddings, search indexes, catalog
CREATE SCHEMA IF NOT EXISTS KNOWLEDGE
    COMMENT = 'Knowledge layer - chunks, embeddings, vector storage, Cortex Search';

-- AGENT: Agent definitions, conversation history, tools
CREATE SCHEMA IF NOT EXISTS AGENT
    COMMENT = 'Agent runtime layer - agent config, conversations, tool registry';

-- GOVERNANCE: Policies, audit logs, lineage tracking
CREATE SCHEMA IF NOT EXISTS GOVERNANCE
    COMMENT = 'Governance layer - access policies, audit logs, data lineage';

-- OBSERVABILITY: Metrics, traces, cost tracking
CREATE SCHEMA IF NOT EXISTS OBSERVABILITY
    COMMENT = 'Observability layer - token usage, latency, cost, agent traces';
