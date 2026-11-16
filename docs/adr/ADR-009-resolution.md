# ADR-009 — Processing resolution strategy

**Status:** Proposed (pending prototype and VRAM benchmarks)

**Deciders:** Architect / Tech Lead, ML Engineer

**Date:** 2026-11-15

## Context

arc42 §14.2 lists resolution as a decision still to be taken: full-page processing versus per-panel/tiling. Full manga pages can be high resolution, which increases VRAM and inference time; tiling reduces memory pressure but risks seams and inconsistency across tile boundaries.

## Decision

Process a page as a whole by default, with optional internal tiling controlled by a resolution profile and VRAM budget. Configurable maximum input dimensions and maximum pixel count guard against memory exhaustion (see arc42 §8.1 security: limit size, dimensions, and pixel count). Resolution profiles (fast / balanced / high quality) map to target output resolution and batch size. Tiling, when enabled, is an internal implementation detail of the colorization pipeline, not a contract change.

## Consequences

### Positive

- Simpler contract and conditioning when processing whole pages.
- Memory safeguards prevent OOM on high-resolution input.
- Quality profiles let users trade speed for fidelity.

### Negative

- Whole-page processing of very large pages may exceed VRAM even with limits; tiling must be tuned per hardware.
- Seam artifacts must be evaluated visually if tiling is used.

## Related

- ADR-008: GPU target (VRAM budget drives resolution limits).
- arc42 §8.1 Security: file size and dimension limits.
- arc42 §14.2 Pending decision: Resolution.
