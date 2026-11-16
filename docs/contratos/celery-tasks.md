# Celery tasks — serializable IDs and parameters

## Rule

Celery task arguments contain only serializable identifiers and primitive parameters. Task arguments never contain ORM model instances, database sessions, file handles, or binary payloads.

## Task argument shape (example)

```json
{
  "task": "colorization.run_colorization",
  "args": [
    "550e8400-e29b-41d4-a716-446655440000"
  ],
  "kwargs": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "page_id": "650e8400-e29b-41d4-a716-446655440001",
    "analysis_id": "750e8400-e29b-41d4-a716-446655440002",
    "palette_id": "850e8400-e29b-41d4-a716-446655440003",
    "resolution_profile": "balanced",
    "seed": null
  }
}
```

## Constraints

- All IDs are UUID strings (see `identifiers.md`).
- Parameters are JSON-serializable primitives: string, integer, float, boolean, null, list, dict.
- Tasks are idempotent: re-executing a task with the same `job_id` must not duplicate artifacts or corrupt state (arc42 §4.2 idempotency, §10.5 recovery).
- Task names follow the dotted module convention: `<domain>.<action>` (e.g. `analysis.run`, `colorization.run_colorization`).
