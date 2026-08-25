# ADR-001: Enterprise Agent Topology

## Status

Accepted

## Context

The lighthouse needs coordinated access to bounded Sales, Finance, analytics, and KPI-knowledge capabilities without duplicating orchestration or governance across autonomous domain agents.

## Decision

Start with one Enterprise KPI Agent that orchestrates bounded tools and capabilities. Do not create one autonomous agent per business domain unless materially different reasoning, security boundaries, workflows, integrations, or state later justify that topology.

## Consequences

- A single control plane owns session context, entitlement checks, intent resolution, ambiguity handling, and routing.
- Sales and Finance remain bounded capabilities with separate semantic contracts.
- New autonomous agents require a later architectural decision supported by concrete isolation needs.
