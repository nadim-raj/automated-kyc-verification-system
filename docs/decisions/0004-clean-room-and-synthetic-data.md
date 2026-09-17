# 0004 — Clean room and synthetic data

**Status:** accepted

## Context

The production system belongs to an employer and cannot be published. The engineering approach is still worth showing.

## Decision

Rewrite the architecture from scratch, generate synthetic fixtures covering the scenarios that matter, and exclude anything proprietary or operationally sensitive ([scope](../scope-and-exclusions.md)).

## Consequences

- **The repository can be public** without touching company property or customer data.
- **It runs.** Synthetic fixtures with deterministic identity seeds mean the demo and tests execute anywhere, with no data and no model.
- **No real performance claims are possible**, and none are made. Synthetic data proves routing logic, not model accuracy.
- **Fixtures do double duty** as the test corpus, so the scenarios that must never be escalated and the ones that must always be are pinned by tests.
