# Security Policy

## Status

This repository is an alpha reference implementation and has **not** undergone an independent security audit.

## Reporting vulnerabilities

Please do not publish exploit details in a public issue before a maintainer has had a reasonable opportunity to assess them. Use GitHub's private vulnerability reporting if enabled; otherwise contact the maintainer through the public contact path on https://digital-fabrica.com and request a private channel.

## Current trust boundaries

- Input JSON is untrusted.
- A configured authority record is not independently verified identity.
- SQLite is a local reference persistence layer, not a hardened multi-tenant database.
- HTTP defaults to loopback and has no built-in authentication/TLS.
- Receipts provide deterministic integrity checks, not non-repudiation or PKI identity proof.
- Policy and credential adapters are not yet production-hardened.

See [docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).
