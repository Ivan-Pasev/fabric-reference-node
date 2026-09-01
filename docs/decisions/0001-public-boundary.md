# ADR-0001: Public repository excludes internal source registries

**Status:** Accepted

The public repository publishes schemas, runtime semantics, synthetic fixtures, adapters/interfaces, and reproducible tests. Project-specific CodexStation claim registries, Evidence Router snapshots, and internal staging databases are not part of the default public genesis.

This avoids confusing source provenance with public authority and prevents accidental publication of project-specific material. Public adapter tests must therefore use synthetic fixtures or separately public upstream resources.
