# Enterprise AI Knowledge Platform — Synthetic Demo Corpus

This directory contains the **synthetic enterprise knowledge corpus** used by the **Enterprise AI Agentic RAG Lighthouse** reference implementation.

The corpus provides structured, unstructured, multimodal, trusted, untrusted, and access-controlled knowledge for demonstrating the Enterprise AI pipeline.

> **Synthetic-data notice:** All documents, datasets, organizations, metrics, market-share figures, customer information, recommendations, policies, and business scenarios contained in this directory are synthetic. They are intended solely for technical demonstration, architecture validation, learning, testing, and portfolio/reference implementation purposes.

## What's Included

The corpus contains PDF enterprise reports, PowerPoint competitive intelligence, Word strategy and Responsible AI/RAG security documents, Excel market intelligence, CSV customer-adoption analytics, HTML enterprise and untrusted web content, an enterprise architecture image, and confidential synthetic content for authorization testing.

Together, these assets support:

**Document & Data Sources → Governance → Parsing / Structured Ingestion → Chunking → Cortex Search / Semantic Views → Cortex Analyst → Cortex Agent → Guardrails → Observability → Evaluation → Trusted Response**

## Knowledge Paths

### Structured Intelligence

`05_Market_Share_2024_2026.xlsx` and `06_Customer_Adoption_Analytics.csv` support:

**Structured Data → Snowflake Tables → Semantic Views → Cortex Analyst → Cortex Agent**

### Unstructured Intelligence

PDF, DOCX, PPTX, and HTML assets support:

**Source Document → Document Registry → AI_PARSE_DOCUMENT / Normalization → Knowledge Chunks → Cortex Search → Cortex Agent**

### Multimodal Intelligence

`08_Enterprise_AI_Knowledge_Architecture.png` is included as an architecture artifact for multimodal knowledge scenarios.

## Security & Governance Test Scenarios

- `11_Untrusted_Analyst_Commentary.html` represents **untrusted external content** for trust-aware retrieval and indirect prompt-injection testing.
- `12_Confidential_Strategic_Assessment.pdf` represents **confidential enterprise knowledge** for authorization-aware retrieval testing.
- `09_Responsible_AI_and_RAG_Security_Standard.docx` provides synthetic enterprise policy evidence for Responsible AI, RAG security, authorization, and prompt-injection controls.

These assets demonstrate that **semantic relevance alone does not determine whether evidence is trusted or authorized for use**.

## Machine-Readable Manifest

`manifest.json` contains machine-readable metadata describing the synthetic corpus and supports repeatable registration, classification, routing, and validation of the knowledge assets.

## Key Demonstration Scenarios

- multimodal enterprise document ingestion;
- governed document registration and provenance;
- structured analytical intelligence;
- governed unstructured retrieval;
- source authority and temporal reasoning;
- semantic, keyword, and hybrid retrieval;
- indirect prompt-injection protection;
- authorization-aware retrieval;
- controlled abstention;
- Cortex Agent planning and multi-tool reasoning;
- grounded response generation;
- execution observability; and
- groundedness, relevance, security, and correctness evaluation.

## Important Usage Notice

The contents of this directory must **not** be interpreted as actual market research, real customer information, official corporate strategy, production security policy, vendor recommendations, or confidential enterprise records.

Synthetic market-share and adoption figures are illustrative and do not represent actual vendor performance. No production credentials, secrets, personal data, proprietary customer information, or other sensitive information should be added to this directory.
