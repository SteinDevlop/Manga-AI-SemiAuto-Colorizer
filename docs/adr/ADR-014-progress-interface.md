# ADR-014 — Progress interface

**Status:** Proposed

**Deciders:** Architect / Tech Lead

**Date:** 2026-11-15

## Context

arc42 §3.2 external interfaces: UI ↔ API carries progress and job notifications over WebSocket, with polling as fallback. arc42 §10.4 performance: the API responds quickly with a job ID and processing continues in the background while the frontend receives updates. arc42 §14.2 lists the progress interface (WebSocket, polling, or both) as a decision still to be taken. Progress events carry job_id, stage, progress, message, and timestamp (see docs/contratos/progress-events.md).

## Decision

Use WebSocket for real-time progress updates from the API to the frontend, with HTTP polling as the fallback when WebSocket is unavailable. Progress events are versioned under /api/v1 and carry job_id, stage, progress (0–100), message, and timestamp in UTC ISO-8601. The same job_id correlates HTTP job creation, WebSocket events, and persisted job state.

## Consequences

### Positive

- Low-latency, push-based updates for a responsive UI.
- Polling fallback keeps the feature working in restricted network/client environments.
- Single job_id correlation across HTTP, WebSocket, and persistence.

### Negative

- WebSocket infrastructure (connection management, reconnection) adds complexity compared to polling alone.

## Related

- arc42 §3.2 External interfaces.
- arc42 §10.4 Performance and resources.
- docs/contratos/progress-events.md.
- arc42 §14.2 Pending decision: Progress interface.
