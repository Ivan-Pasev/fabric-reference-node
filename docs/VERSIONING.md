# Versioning surfaces

Fabric Reference Node has separate version surfaces. They are intentionally not collapsed.

- **Software package:** `0.1.0` — first public OSS packaging/release line.
- **Reference Node object schema:** `1.0.0` — the object vocabulary carried in `reference-node.schema.json`.
- **Transport / durable-transition / transfer-governance contract lineage:** `0.3.0` — inherited from the bounded internal R1 implementation that preceded public packaging.
- **Transfer receipt contract:** `0.2.0` — retained for compatibility with the explicit source-transfer boundary.

A higher contract number does not mean the public software is more mature than its package version, and a software release never automatically promotes scientific, formal, security, compliance, or institutional authority.

Future changes should version the narrowest affected surface and provide migration notes for semantic incompatibilities.
