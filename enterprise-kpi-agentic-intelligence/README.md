# Enterprise KPI Agentic Intelligence

Interview-grade Snowflake lighthouse project for rebuilding trust in enterprise KPIs through governed data products, certified metrics, bounded semantic views, and controlled agent orchestration.

## Business Problem

Enterprise KPI definitions have drifted across business domains, creating multiple legitimate versions of terms such as `bookings`. The platform must distinguish authorization from intent and must clarify semantic ambiguity rather than guess.

## Architecture Objective

`Governed Data → Certified Metrics → Semantic Intelligence → Enterprise Agent → Trusted Answer → Audit/Evidence`

## Technology Stack

- Snowflake
- dbt
- Snowflake Semantic Views
- Cortex Analyst
- Cortex Search
- Cortex Agents
- Apache Airflow (later increment)
- Git / GitHub / Codex

## Implementation Status

- I0 — Repository Bootstrap: IN PROGRESS
- I1–I15: NOT STARTED

## Engineering Rule

`DESIGN → BUILD → EXECUTE → VERIFY → EVIDENCE → PASS`

An increment is not complete merely because code exists.

## Flagship Acceptance Scenario

User asks: `What were bookings this quarter?`

If multiple certified and authorized KPI concepts match, the platform must ask for clarification and must not execute an analytical query until the intended KPI is resolved.
