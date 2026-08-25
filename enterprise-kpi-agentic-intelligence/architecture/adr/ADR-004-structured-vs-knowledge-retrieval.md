# ADR-004: Structured Analytics vs Knowledge Retrieval

## Status

Accepted

## Context

Quantitative KPI answers and explanatory governance knowledge require different retrieval modes and authoritative sources.

## Decision

Use Cortex Analyst for quantitative governed analytics and Cortex Search for KPI definitions, rationale, policy, and provenance. The Enterprise KPI Agent orchestrates between them.

## Consequences

- Certified Semantic Views and trusted marts are authoritative for quantitative truth.
- The certified KPI registry is authoritative for definition, ownership, status, and version.
- Governed KPI knowledge supplies rationale, policy, and decision provenance.
- General model knowledge is never authoritative for enterprise KPI facts.
