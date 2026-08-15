# Enterprise AI Knowledge Platform --- Synthetic Demo Corpus

This directory contains the **synthetic enterprise knowledge corpus**
used by the **Enterprise AI Knowledge Platform Using Agentic RAG**
reference implementation.

The corpus provides structured, unstructured, multimodal, trusted,
untrusted, and access-controlled knowledge for demonstrating the
Enterprise AI pipeline.

> **Synthetic-data notice:** All documents, datasets, organizations,
> metrics, market-share figures, customer information, recommendations,
> policies, and business scenarios contained in this directory are
> synthetic. They are intended solely for technical demonstration,
> architecture validation, learning, testing, and portfolio/reference
> implementation purposes.

## What's Included

The corpus contains:

-   PDF enterprise reports
-   PowerPoint competitive intelligence
-   Word strategy and Responsible AI / RAG security documents
-   Excel market intelligence
-   CSV customer-adoption analytics
-   HTML enterprise and untrusted web content
-   An enterprise architecture image
-   Confidential synthetic content for authorization testing

Together, these assets support the following implementation journey:

**Document & Data Sources → Governance → Parsing / Structured Ingestion
→ Chunking → Cortex Search / Semantic Views → Cortex Analyst → Cortex
Agent → Guardrails → Observability → Evaluation → Trusted Response**

## Knowledge Paths

The corpus intentionally supports multiple governed knowledge paths.

### Structured Intelligence

`05_Market_Share_2024_2026.xlsx` and
`06_Customer_Adoption_Analytics.csv` support governed quantitative
analytics through:

**Structured Data → Snowflake Tables → Semantic Views → Cortex Analyst →
Cortex Agent**

### Unstructured Intelligence

PDF, DOCX, PPTX, and HTML assets support:

**Source Document → Document Registry → AI_PARSE_DOCUMENT /
Normalization → Knowledge Chunks → Cortex Search → Cortex Agent**

### Multimodal Intelligence

`08_Enterprise_AI_Knowledge_Architecture.png` is included as an
architecture artifact for multimodal knowledge scenarios.

## Security & Governance Test Scenarios

The corpus also contains deliberately designed assets for Enterprise AI
assurance testing.

-   `11_Untrusted_Analyst_Commentary.html` represents **untrusted
    external content** and supports trust-aware retrieval and indirect
    prompt-injection testing.
-   `12_Confidential_Strategic_Assessment.pdf` represents **confidential
    enterprise knowledge** and supports authorization-aware retrieval
    testing.
-   `09_Responsible_AI_and_RAG_Security_Standard.docx` provides
    synthetic enterprise policy evidence for Responsible AI, RAG
    security, authorization, and prompt-injection controls.

These assets allow the implementation to demonstrate that **semantic
relevance alone does not determine whether evidence is trusted or
authorized for use**.

## Corpus Documentation

For detailed information about individual files, classifications, trust
levels, security scenarios, and intended demonstration cases, see:

**`DEMO_CORPUS_GUIDE.md`**

## Machine-Readable Manifest

**`manifest.json`** contains machine-readable metadata describing the
synthetic corpus and supports repeatable registration, classification,
routing, and validation of the knowledge assets.

## Key Demonstration Scenarios

The corpus supports:

-   multimodal enterprise document ingestion;
-   governed document registration and provenance;
-   structured analytical intelligence;
-   governed unstructured retrieval;
-   source authority and temporal reasoning;
-   semantic, keyword, and hybrid retrieval;
-   indirect prompt-injection protection;
-   authorization-aware retrieval;
-   controlled abstention;
-   Cortex Agent planning and multi-tool reasoning;
-   grounded response generation;
-   execution observability;
-   groundedness, relevance, security, and correctness evaluation.

## Important Usage Notice

The contents of this directory must **not** be interpreted as:

-   actual market research or analyst data;
-   real customer or adoption information;
-   official corporate strategy;
-   production security policy;
-   vendor recommendations;
-   confidential enterprise records.

Synthetic market-share and adoption figures are illustrative and do not
represent actual vendor performance.

No production credentials, secrets, personal data, proprietary customer
information, or other sensitive information should be added to this
directory.

------------------------------------------------------------------------

This corpus accompanies the **Enterprise AI Knowledge Platform Using
Agentic RAG** reference implementation and is designed to make the
solution reproducible from **source knowledge through governed Agentic
AI response and evaluation**.
