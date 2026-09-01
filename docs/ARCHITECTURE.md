# Architecture

## Design objective

Fabric Reference Node models a consequential action as a recoverable chain rather than an opaque model output.

```text
source evidence
    ↓
claims / interpretation
    ↓
policy + authority context
    ↓
invariant results
    ↓
machine assessment: PASS | HOLD | FAIL
    ↓
institutional decision
    ↓
trace + deterministic receipt
    ↓
persistent effective state
    ↓
continuation / supersession / retraction
```

## Core objects

`Artifact`, `Claim`, `Evidence`, `Policy`, `InstitutionalAuthority`, `Invariant`, `Assessment`, `Decision`, `Trace`, `ContinuationLink`, `Receipt`, and transition events.

## State model

Base claim bytes are immutable. Governance changes are represented in a separate effective-state overlay.

The transition store tracks two roots:

- `effective_state_root` — base node state plus active overlays;
- `history_root` — append-only hash chain of state transitions.

The composite `state_root` includes both. A rollback can restore an earlier effective state, but the history root advances, preserving the fact that a retraction and rollback occurred.

## Dependency semantics

Applied retraction propagates only through declared **dependency** edges. Contradiction or semantic-neighbor edges must not be treated as dependency propagation unless explicitly modeled as such.

## Interoperability boundary

External systems enter through adapters. Reading or staging an upstream object confers no authority in the local node. Any semantic projection should be explicit and reviewable.
