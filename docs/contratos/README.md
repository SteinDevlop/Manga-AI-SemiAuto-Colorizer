# Data contracts and DTOs

This directory documents the explicit contracts between the backend, the Celery workers, and the AI engine. The contracts are intentionally kept independent of any ORM model: the frontend and the AI engine never import backend ORM objects.

## Contracts

| Contract | File | Covers |
|----------|------|--------|
| Identifiers | `identifiers.md` | UUIDs for all entities and jobs |
| Timestamps | `timestamps.md` | UTC persistence, ISO-8601 in the API |
| API versioning | `api-versioning.md` | `/api/v1` prefix and versioning |
| Errors | `errors.md` | `code`, `message`, `details`, `request_id` error envelope |
| Artifacts | `artifacts.md` | `artifact_id` references, never client paths |
| Celery tasks | `celery-tasks.md` | Serializable task IDs and parameters |
| Progress events | `progress-events.md` | `job_id`, `stage`, `progress`, `message`, `timestamp` |
| DTO schemas | `dto-schemas.md` | Versioned DTOs and AI engine protocol interfaces |

## Source of truth

These contracts are derived from:

- `docs/arc42.md` — §3.2 external interfaces, §5.4 AI engine contract, §8.2 file and artifact handling, §8.3 observability and traceability, §14.2 pending decisions.
- `docs/planes/P0-arquitectura-bootstrap.md` — Contracts that must be agreed (UUIDs, UTC ISO-8601, `/api/v1`, error envelope, `artifact_id`, serializable Celery tasks, progress events, no shared ORM models).

## Rule

No backend ORM model is shared with the frontend or the AI engine. All cross-process data crosses the boundary as versioned DTOs or plain serializable structures.
