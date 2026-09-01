# Threat Model — Draft 0.1

## Assets

- claim/evidence lineage;
- institutional authority records;
- policy and invariant context;
- decision traces and receipts;
- effective state and transition history.

## Adversaries / failure classes

1. forged or stale authority;
2. evidence substitution or omission;
3. policy confusion / wrong jurisdiction;
4. invariant bypass;
5. replay of a valid receipt against changed input;
6. deletion or rewriting of adverse history;
7. semantic inflation during cross-system transfer;
8. dependency poisoning;
9. unauthorized local HTTP access;
10. database corruption or rollback race.

## Current mitigations

- immutable IDs with collision failure;
- deterministic canonical hashes;
- explicit scope checks;
- `HOLD` for unresolved required inputs;
- machine/human decision separation;
- compare-and-swap state roots for transitions;
- append-only transition hash chain;
- no automatic cross-system authority transfer.

## Open security work

Authentication, TLS, credential verification, database hardening, multi-user authorization, secrets handling, cryptographic signatures, fuzzing, denial-of-service analysis, backup/recovery, and independent audit remain open.
