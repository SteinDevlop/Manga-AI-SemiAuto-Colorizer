# ADR-011 — Persistence and retention policy

**Status:** Proposed

**Deciders:** Architect / Tech Lead

**Date:** 2026-11-15

## Context

arc42 §2.1 constraints 7–8: originals and generated files are stored on local disk; PostgreSQL holds metadata and relations; Redis is the broker, not permanent result storage. arc42 §7.3: PostgreSQL uses a persistent volume for metadata; storage uses persistent directories for originals and results; models are a separate read-only directory when viable; `.env` local configuration is excluded from Git; backups export the database and copy manifests/artifacts; cleanup has a configurable policy for temporaries and never deletes originals or results without confirmation. arc42 §8.2: artifacts are not stored as PostgreSQL blobs unless concretely justified. arc42 §14.2 lists persistence (retention policy for originals, temporaries, results) as a decision still to be taken.

## Decision

Metadata and state in PostgreSQL; binaries (originals, panels, masks, previews, results, model weights) on the local filesystem, referenced by stable artifact_id and storage paths, never as database blobs. A configurable retention policy applies only to temporary files; originals and results are never deleted or purged without explicit user confirmation. Backups consist of a database export plus a copy of manifests and artifact storage.

## Consequences

### Positive

- Clear separation of structured metadata (PostgreSQL) and large binaries (filesystem).
- Safe default: originals and results are preserved unless explicitly confirmed for deletion.
- Coordinated backup strategy (DB export + artifact copy).

### Negative

- Filesystem and database can drift; requires orphan cleanup and reconciliation tooling.
- Retention policy must be configured before production use to avoid unbounded disk growth.

## Related

- ADR-003: PostgreSQL for metadata, filesystem for images.
- arc42 §7.3 Persistence and backups.
- arc42 §8.2 File and artifact handling.
- arc42 §14.2 Pending decision: Persistence.
