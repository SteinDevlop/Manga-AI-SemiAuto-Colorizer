# Timestamps — UTC and ISO-8601

## Persistence

All timestamps are stored in PostgreSQL in UTC (timezone-aware). No local time or server-dependent time zone is persisted.

## API

All timestamps exchanged over the API (REST and WebSocket) are formatted as UTC ISO-8601 strings with the `Z` suffix:

```
2026-11-15T10:30:00Z
```

## Fields in scope

| Field | Meaning |
|-------|---------|
| created_at | Resource creation time (UTC) |
| updated_at | Last modification time (UTC) |
| started_at | Job/worker stage start time (UTC) |
| finished_at | Job/worker stage completion time (UTC) |
| timestamp | Progress event emission time (UTC) |

## Constraints

- Clients must not send timestamps with non-UTC offsets as the authoritative value; the server normalizes to UTC and rejects ambiguous or malformed timestamps with a 400 error.
- Timestamps are never used as business identifiers; use UUIDs for identity (see `identifiers.md`).
