# Error contract

## Error envelope

Every API error response (REST and WebSocket) uses this JSON envelope:

```json
{
  "code": "validation_error",
  "message": "The page_id does not reference an existing page.",
  "details": {
    "field": "page_id",
    "reason": "not_found"
  },
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Required | Meaning |
|-------|------|----------|---------|
| code | string | yes | Stable, machine-readable error code (snake_case). |
| message | string | yes | Human-readable description of the error. |
| details | object | no | Structured additional context (field names, reasons, constraints). |
| request_id | string | yes | UUID correlating the error to the originating request and logs. |

## HTTP status mapping (examples)

| HTTP status | code example | Meaning |
|-------------|--------------|---------|
| 400 | `validation_error` | Malformed or invalid request. |
| 401 | `unauthenticated` | Missing or invalid authentication. |
| 403 | `forbidden` | Authenticated but not authorized. |
| 404 | `not_found` | Referenced resource does not exist. |
| 409 | `precondition_failed` | Business precondition not met (e.g. analysis not approved). |
| 422 | `unprocessable` | Semantically valid but cannot be processed. |
| 429 | `rate_limited` | Too many requests. |
| 500 | `internal_error` | Unexpected server error. |
| 503 | `service_unavailable` | Dependency (queue, model worker) unavailable. |

## Constraints

- `code` values are stable across versions so clients can handle them programmatically.
- `message` may change between versions; clients must not depend on its exact text.
- `request_id` is generated per request and logged server-side for traceability (see arc42 §8.3).
- Error envelopes never expose stack traces, file system paths, or ORM internals to the client.
