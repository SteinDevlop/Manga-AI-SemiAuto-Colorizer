# Progress events

## Rule

Job progress is pushed to the frontend as events with this shape:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "stage": "preprocessing",
  "progress": 35,
  "message": "Loading masks and references",
  "timestamp": "2026-11-15T10:30:00Z"
}
```

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| job_id | UUID string | yes | The colorization job the event belongs to. |
| stage | string | yes | Current processing stage (e.g. `pending`, `preprocessing`, `colorizing`, `refining`, `completed`, `failed`, `cancelled`). |
| progress | integer | yes | Progress within the stage, 0–100. |
| message | string | yes | Human-readable status message. |
| timestamp | UTC ISO-8601 | yes | Event emission time. |

## Delivery

- Primary channel: WebSocket (`/api/v1/ws/jobs/{job_id}/progress`).
- Fallback channel: HTTP polling of the job endpoint.
- `job_id` correlates the event with the HTTP-created job, persisted job state, and logs (arc42 §8.3).

## Stages

Stages map to the colorization job state machine (docs/architecture/06-colorization-states.mmd). Internal sub-stages may be added without changing the public `stage` values exposed to the frontend.
