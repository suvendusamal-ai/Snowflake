# ADR-002: Domain Semantic Views

## Status

Accepted

## Context

A single enterprise-wide semantic model would couple distinct business grains, definitions, ownership, and change cycles and could obscure the legitimate difference between Sales Bookings and Recognized Revenue.

## Decision

Use bounded Semantic Views per coherent business domain. The initial domains are Sales and Finance, exposing `SALES_BOOKINGS` and `RECOGNIZED_REVENUE` respectively under the approved business trust model.

## Consequences

- Domain ownership and certification remain explicit.
- Cross-domain orchestration occurs through the Enterprise KPI Agent rather than an oversized semantic model.
- Shared dimensions require governed alignment without collapsing distinct KPI meanings.
