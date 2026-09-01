# Fabric Reference Node

[![CI](https://github.com/Ivan-Pasev/fabric-reference-node/actions/workflows/ci.yml/badge.svg)](https://github.com/Ivan-Pasev/fabric-reference-node/actions/workflows/ci.yml)

**Open infrastructure for evidence-bearing, authority-aware, invariant-checked AI and agent actions.**

Fabric Reference Node is a small, auditable runtime for a problem that becomes unavoidable when software agents act across tools, organizations, policies, and human decision boundaries:

> **Who authorized this action, what evidence supported it, which policy and invariants were checked, what did the machine conclude, what did the human decide, what changed, and can the result be reconstructed or reversed?**

The project is the public reference implementation of a bounded part of **Digital Fabrica Theory 2.0 (DFT 2.0)**. You do **not** need to accept the wider DFT research program to use or evaluate this repository.

## What it does

A canonical workflow is:

```text
Evidence
  → policy / authority checks
  → invariant checks
  → machine outcome: PASS | HOLD | FAIL
  → human / institutional decision
  → durable trace + receipt
  → persistent state
  → retraction / rollback without history erasure
```

The runtime deliberately keeps three things separate:

1. **machine obligation state** — `PASS / HOLD / FAIL`;
2. **institutional decision** — e.g. `APPROVE / REJECT / ESCALATE / DEFER / UNKNOWN`;
3. **claim authority/evidence state** — separately typed and never auto-promoted by execution.

`PASS` is therefore **not** approval, proof, compliance, or truth.

## 60-second start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
python examples/governed_decision.py
```

Run the local HTTP node:

```bash
fabric-reference-node --db ./node.sqlite --port 8787
```

Then:

```bash
curl http://127.0.0.1:8787/v1/health
curl http://127.0.0.1:8787/v1/capabilities
```

## Verify

```bash
python -m unittest discover -s tests -v
```

Optional schema validation:

```bash
pip install -e '.[dev]'
python scripts/validate_schemas.py
```

The public genesis CI runs the install, test suite, schema checks, and synthetic governed-decision example on Python 3.11 and 3.12. See [`evidence/`](evidence/) for the bounded genesis evidence envelope.

## Current maturity

`0.1.0` is a **bounded local executable reference candidate**.

Current evidence supports:

- immutable object IDs and fail-closed collisions;
- explicit claim dependency closure;
- evidence / policy / invariant resolution;
- machine vs human decision separation;
- deterministic receipts;
- non-mutating retraction simulation;
- SQLite-backed state persistence;
- applied retraction as an effective-state overlay;
- dependency-only suspension propagation;
- append-only transition history;
- rollback that restores effective state **without erasing history**;
- local HTTP transport.

It does **not** establish production security, legal/regulatory compliance, formal proof, scientific validity, fairness, external assurance, or production readiness. See [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md).

A known open publication gap is full runtime-object instance conformance against every required field in the interchange schema. It is tracked publicly in [issue #1](https://github.com/Ivan-Pasev/fabric-reference-node/issues/1).

## Why this is open source

The core coordination primitives—provenance, authority, policy binding, invariant checks, receipts, rollback semantics, and interoperable traces—are more useful if they are inspectable and portable across vendors and institutions.

The project aims to **compose with** mature standards and protocols rather than replace them. Planned adapters include policy-as-code, verifiable credentials, MCP/A2A-style agent transports, and standards-based provenance formats.

## Architecture

```text
┌──────────────────────────────────────────────┐
│              Fabric Reference Node           │
├──────────────────────────────────────────────┤
│ Artifact / Claim / Evidence registry         │
│ Policy + institutional authority             │
│ Invariant evaluation                         │
│ Machine assessment                           │
│ Human / institutional decision               │
│ Trace + receipt                              │
│ Continuation / supersession                  │
│ Retraction + reversible effective state      │
│ SQLite persistence + local HTTP              │
└──────────────────────────────────────────────┘
```

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). Version surfaces are explained in [docs/VERSIONING.md](docs/VERSIONING.md).

## Companion projects

- **Cross-Principal Agent Witness** — adversarial/research benchmark for delegation, provenance, scope and revocation: https://github.com/Ivan-Pasev/cross-principal-agent-witness
- **Fabric Mesh Protocol** — federation/interoperability research track: https://github.com/Ivan-Pasev/fabric-mesh-protocol
- **Digital Fabrica Theory 2.0** — wider architecture and research program: https://digital-fabrica.com

These projects do not silently inherit one another's evidence or authority.

## Funding philosophy

The repo is **not built for a single fellowship or grant**. Funding should finance public evidence-producing work packages—interoperability, security, formalization, documentation, adoption, and maintenance—without changing the technical truth of the project. See [docs/FUNDING.md](docs/FUNDING.md).

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md), the [roadmap](ROADMAP.md), and the [open issues](https://github.com/Ivan-Pasev/fabric-reference-node/issues). Small reproducible examples, adapters, adversarial cases, security review, and documentation improvements are especially welcome.

## License

Apache License 2.0. See [LICENSE](LICENSE).
