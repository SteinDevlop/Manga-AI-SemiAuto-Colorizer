# API versioning — `/api/v1`

## Rule

All backend REST endpoints are versioned under the `/api/v1` path prefix. The version is part of the URL path, not a header.

## Example

```
GET  /api/v1/projects/{project_id}
POST /api/v1/pages
POST /api/v1/colorizations
POST /api/v1/analysis/{id}/approve
```

## WebSocket

Progress and notification WebSocket endpoints are also versioned:

```
ws://localhost:8000/api/v1/ws/jobs/{job_id}/progress
```

## Constraints

- Breaking changes require a new path version (e.g. `/api/v2`); minor additive changes remain within `/api/v1`.
- The frontend targets exactly one API version at a time.
- No unversioned `/api` endpoints are exposed.
