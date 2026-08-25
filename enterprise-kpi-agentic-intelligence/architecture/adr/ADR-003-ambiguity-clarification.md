# ADR-003: Ambiguity Clarification

## Status

Accepted

## Context

An authorized user may use `bookings` when multiple certified and effective KPI concepts legitimately match. Authorization determines access but does not establish intended business meaning.

## Decision

When multiple authorized, certified, and effective KPI concepts legitimately match unresolved intent, clarify rather than guess. Do not use RBAC to infer intent or depend blindly on an invented confidence score. No final analytical query executes until the metric is resolved.

Test native Cortex behavior first. If deterministic enforcement is not sufficiently guaranteed, introduce a lightweight governed `RESOLVE_KPI` capability in a later increment.

## Consequences

- The flagship multi-candidate path returns a discriminating clarification.
- Zero candidates return Not Found or clarification; one valid candidate proceeds to tool routing.
- Any later resolver must use governed vocabulary and certification metadata rather than model knowledge as authority.
