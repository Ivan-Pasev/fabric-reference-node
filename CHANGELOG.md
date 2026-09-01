# Changelog

## 0.1.0 — Public genesis candidate

- extracted public Reference Node core from the bounded DFT 2.0 R1 local implementation;
- added installable Python package and local HTTP CLI;
- included public schemas and OpenAPI contract;
- retained durable retraction / append-only rollback semantics;
- added synthetic example and public regression tests;
- added explicit claim, governance, security, and funding boundaries;
- intentionally excluded internal CodexStation/Evidence Router snapshots;
- normalized inherited OpenAPI schema-reference filenames before public genesis;
- added schema-complete canonical runtime fixtures and CI instance-validation against the full Reference Node interchange schema;
- hardened typed registry admission to fail closed on missing or unexpected fields.
