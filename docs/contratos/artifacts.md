# Artifacts — `artifact_id`

## Rule

Artifacts are referenced exclusively by a server-generated `artifact_id`. Clients never supply or construct file paths for artifacts; arbitrary client-provided paths are rejected.

## Artifact record

| Field | Type | Meaning |
|-------|------|---------|
| artifact_id | UUID | Stable artifact identifier |
| type | string | `original`, `panel`, `mask`, `reference`, `preview`, `result` |
| sha256 | string | SHA-256 hash of the file contents |
| format | string | File format (e.g. `png`, `jpg`, `webp`) |
| width | integer | Pixel width |
| height | integer | Pixel height |
| size_bytes | integer | File size in bytes |
| page_id | UUID | Related page (nullable) |
| job_id | UUID | Related colorization job (nullable) |
| created_at | UTC timestamp | Creation time |
| pipeline_version | string | Version of the pipeline that produced the artifact |

## Constraints

- Binaries are stored on the local filesystem, not as PostgreSQL blobs (see ADR-011 and arc42 §8.2).
- `artifact_id` is opaque and stable; the underlying storage path is an implementation detail.
- Artifacts are versioned: re-running a stage (e.g. re-segmentation) produces a new artifact version rather than overwriting.
