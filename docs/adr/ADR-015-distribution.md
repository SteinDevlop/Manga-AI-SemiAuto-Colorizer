# ADR-015 — Distribution

**Status:** Proposed (pending product confirmation)

**Deciders:** Architect / Tech Lead

**Date:** 2026-11-15

## Context

arc42 §1.5: the application is a local web app, initially single-user and single-machine. arc42 §7.1: initial deployment is local via Docker Compose or local processes. arc42 §1.4 non-goals: multi-user collaboration and distributed deployment. arc42 §14.2 lists distribution (run from source only, or local installer) as a decision still to be taken.

## Decision

MVP: run from source code locally (Docker Compose or local processes), single-user, single-machine. A packaged local installer is deferred to post-MVP. No cloud distribution or remote access is in scope for P0.

## Consequences

### Positive

- Aligns with the local-only, privacy-by-default architecture.
- Minimal distribution complexity in P0; focus remains on the core pipeline.

### Negative

- Less accessible for non-technical users until a packaged installer is available.

## Related

- arc42 §7.1 Initial local deployment.
- arc42 §1.4 Non-goals.
- arc42 §14.2 Pending decision: Distribution.
