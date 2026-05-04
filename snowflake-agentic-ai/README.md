# Snowflake Agentic AI - Enterprise Demo

Features:
- Cortex Analyst (Text-to-SQL)
- Cortex Search (RAG)
- Fraud Detection
- Streamlit UI
- Duo Authentication

# 🏦 Snowflake Agentic AI – Banking Intelligence System

## 📌 Overview

This project demonstrates a **5-layer enterprise Agentic AI architecture on Snowflake**, combining:

- Deterministic data processing (SQL + UDF)
- Retrieval-Augmented Generation (Cortex Search)
- LLM-based reasoning (Cortex COMPLETE)
- Hybrid orchestration (Python + Snowpark)

The system enables **fraud detection, customer risk analysis, and explainable AI insights** over banking datasets.

---

## 🧠 Architecture

The solution follows a **5-layer Agentic AI architecture**:

| Layer | Implementation |
|------|--------------|
| Guardrails & Gateway | Streamlit UI + Intent Routing + Snowflake RBAC |
| Orchestration | Python (`tool_router.py`) + Snowpark |
| Tools & MCP | SQL, UDFs, Cortex Analyst, Cortex Search, Cortex COMPLETE |
| Memory & Context | Snowflake Tables + Cortex Search (Vector Store) |
| Observability | AGENT_LOGS + Streamlit Trace + Query History |

---

## 🏗️ Architecture Diagram

```mermaid
flowchart TD

    A[User / Streamlit UI] --> B[Guardrails & Gateway]

    B --> C[Orchestrator<br/>tool_router.py]

    C --> D1[SQL Engine<br/>Snowflake Tables]
    C --> D2[UDF<br/>FRAUD_SCORE]
    C --> D3[Cortex Search<br/>RAG]
    C --> D4[Cortex COMPLETE<br/>LLM]
    C --> D5[Cortex Analyst<br/>Text-to-SQL]

    D1 --> E[Memory Layer<br/>Transactions / Customers / Accounts]
    D3 --> F[Vector Store<br/>BANKING_DOCS]

    E --> G[Response Builder]
    F --> G
    D4 --> G

    G --> H[Streamlit UI Output]

    C --> I[Observability<br/>AGENT_LOGS]
    I --> J[Snowflake Query History]