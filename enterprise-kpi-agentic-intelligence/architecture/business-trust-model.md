# Business Trust Model

## Purpose

This document is the business and governance contract for the lighthouse KPIs. It defines their meaning before any data, transformation, semantic, or agent implementation. The lighthouse demonstrates management-reporting semantics only and does not claim formal GAAP or IFRS compliance.

## Sales Bookings business contract

| Field | Contract |
|---|---|
| Metric ID | `SALES_BOOKINGS` |
| Business purpose | Measure qualifying commercial demand accepted by the organization. |
| Business definition | Value of commercially accepted qualifying customer commitments. |
| Grain | One order line and booking event. Reversals and amendments are separate immutable events. |
| Calculation concept | Sum qualifying booking, reversal, and adjustment event values for the reporting period. |
| Inclusion | Approved customer commitments that satisfy the commercial booking policy and have a measurable value. |
| Exclusion | Draft quotes, non-binding pipeline, rejected or duplicate events, and internal/test transactions. |
| Period attribution | Calendar quarter containing the commercial acceptance or booking effective date. |
| Owner | Chief Revenue Officer or delegated Sales executive. |
| Steward | Sales Operations or Revenue Operations data steward. |
| Expected consumers | Sales leadership, Revenue Operations, commercial planning, and executive reporting. |
| Synonyms | Sales bookings, commercial bookings, order bookings, booked business, and `bookings` where approved vocabulary supports the association. |
| Commonly confused with | Recognized revenue, billings, pipeline, and contracted value. |

## Recognized Revenue business contract

| Field | Contract |
|---|---|
| Metric ID | `RECOGNIZED_REVENUE` |
| Business purpose | Measure value qualifying for Finance recognition during a reporting period. |
| Business definition | Value qualifying for recognition after the approved delivery, service, or recognition condition has been satisfied. |
| Grain | One order line, recognition event, and accounting period. An order line may have multiple recognition events. |
| Calculation concept | Sum qualifying recognition and recognition-adjustment event values for the reporting period. |
| Inclusion | Events with an eligible customer commitment and a satisfied, approved recognition condition. |
| Exclusion | Commercial commitments alone, undelivered goods, unperformed services, duplicate events, and amounts not yet eligible for recognition. |
| Period attribution | Calendar quarter containing the recognition date or assigned accounting period. |
| Owner | Chief Financial Officer or delegated Finance executive. |
| Steward | Finance Controllership or Revenue Accounting data steward. |
| Expected consumers | Finance leadership, Controllership, FP&A, executive reporting, and governance teams. |
| Synonyms | Recognized revenue, Finance revenue, revenue, and `bookings` only where approved enterprise vocabulary supports the association. |
| Commonly confused with | Sales bookings, billings, cash receipts, deferred revenue, and contracted value. |

## Why the totals differ

The two metrics answer different questions: `SALES_BOOKINGS` measures qualifying commercial commitments; `RECOGNIZED_REVENUE` measures value after the qualifying recognition condition is satisfied.

| Conceptual event | `SALES_BOOKINGS` | `RECOGNIZED_REVENUE` |
|---|---:|---:|
| 100 booked and fully recognized in Q1 | Q1: +100 | Q1: +100 |
| 120 booked in Q1 and recognized in Q2 | Q1: +120 | Q2: +120 |
| 80 booked in Q1, then cancelled before recognition in Q2 | Q1: +80; Q2: -80 | 0 |
| 200 booked in Q1; 100 qualifies for recognition in Q1 and 100 in Q2 | Q1: +200 | Q1: +100; Q2: +100 |
| Regional commitment booked in one period and recognized in another | Booking event follows its approved commercial treatment | Recognition event follows its approved Finance treatment |

Cancellation never rewrites the original booking. It creates a negative event in the cancellation period. Amendments likewise create positive or negative adjustment events.

## KPI governance metadata contract

Every governed KPI version requires:

| Field | Required meaning |
|---|---|
| `metric_id` | Stable machine identifier for the governed concept. |
| `metric_name` | Human-readable business name. |
| `business_definition` | Precise meaning of the metric. |
| `domain` | Accountable business domain. |
| `owner` | Role accountable for the definition. |
| `steward` | Role responsible for operational governance. |
| `calculation_description` | Business calculation and event timing rules. |
| `source_data_product` | Governed input product expected to implement the definition. |
| `certification_status` | Current lifecycle state. |
| `effective_from` | First date governed by this version. |
| `effective_to` | Last date governed by this version; open while current. |
| `version` | Immutable definition version. |
| `synonyms` | Approved vocabulary used for discovery and intent matching. |
| `commonly_confused_with` | Similar concepts that require distinction. |
| `approval_reference` | Governing policy, decision, ticket, or ADR reference. |
| `business_reason` | Reason the definition exists or changed. |
| `created_at` | Metadata creation timestamp. |
| `updated_at` | Latest metadata update timestamp. |

## Certification lifecycle

`DRAFT → UNDER_REVIEW → CERTIFIED → DEPRECATED`

- `DRAFT`: incomplete and non-authoritative.
- `UNDER_REVIEW`: awaiting governance approval and non-authoritative.
- `CERTIFIED`: approved, effective, versioned, and eligible for authoritative downstream semantic and agent use.
- `DEPRECATED`: retained for history but unavailable as the preferred definition for new questions.

Only an effective `CERTIFIED` metric version is authoritative. Certification does not resolve user intent and does not permit a downstream capability to choose arbitrarily between legitimate candidates.

## Decision provenance contract

Decision provenance must record why the KPI exists, why its definition and calculation were chosen, its owner and steward, who approved it, its approval reference, effective version, predecessor, reason for change, and why it differs from similarly named KPIs. Prior versions remain historically traceable and must not be silently rewritten.

Decision provenance is separate from technical lineage:

- **Decision Provenance:** business reason → definition decision → approval → effective version
- **Technical Lineage:** source → dbt → mart → Semantic View → generated SQL → answer

Technical lineage will be implemented later.

## Ambiguity and clarification contract

For the question `What were bookings this quarter?`, the term `bookings` may match multiple governed concepts where supported by approved enterprise vocabulary.

If `SALES_BOOKINGS` and `RECOGNIZED_REVENUE` are both authorized, certified, effective, and legitimate candidates, the required behavior is:

`multiple authorized + certified + effective candidate concepts → CLARIFY`

The clarification must distinguish commercially accepted commitments from value satisfying Finance recognition conditions. Authorization establishes access, not intent. The system must not arbitrarily choose a metric or execute the final analytical query until metric intent is resolved.

## Approved assumptions

- The canonical metrics are `SALES_BOOKINGS` and `RECOGNIZED_REVENUE`.
- The lighthouse models management-reporting semantics only.
- Sales Bookings uses the commercial acceptance or booking effective date.
- Recognized Revenue uses the recognition date or accounting period.
- Calendar quarters are the reporting calendar.
- Event history is immutable.
- Cancellations create negative reversal events.
- Amendments create positive or negative adjustment events.
- Only effective `CERTIFIED` versions are authoritative downstream.
- Approved vocabulary may associate `bookings` with multiple governed concepts.
- Decision provenance and technical lineage remain separate contracts.

## Downstream implementation obligations

- **I4 synthetic data:** represent booking, recognition, cancellation, adjustment, partial-recognition, period-boundary, and regional events without overwriting history.
- **I5 dbt trusted products:** implement the approved grains, rules, event dates, and immutable adjustments without redefining the KPIs.
- **I6 KPI registry:** store the required metadata, versions, lifecycle, vocabulary, confusion relationships, and approval references.
- **I8 Semantic Views:** expose the two concepts as distinct metrics and only use effective certified versions.
- **I9 KPI knowledge:** explain definitions, ownership, provenance, synonyms, and differences using governed metadata.
- **I10 Enterprise Agent:** separate authorization from intent and consider only authorized, effective, certified candidates authoritative.
- **I11 ambiguity resolution:** clarify multiple legitimate matches before executing the final analytical query.
- **I12 evaluation:** verify explicit selection, required clarification, no arbitrary choice, correct period behavior, and preservation of immutable events.

Later increments must conform to this contract. A business-semantic change requires a new governed metric version and updated decision provenance rather than a silent implementation change.
