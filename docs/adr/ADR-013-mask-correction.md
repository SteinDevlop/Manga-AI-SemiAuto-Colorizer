# ADR-013 — Mask correction scope

**Status:** Proposed (pending UX and benchmark validation)

**Deciders:** Architect / Tech Lead, UX, ML Engineer

**Date:** 2026-11-15

## Context

arc42 §1.5 users include the end user who needs to correct identities, palettes, and masks proposed by the AI (quality attribute: usability, media-alta). arc42 §8.6 human-in-the-loop: the system must allow correcting or replacing masks. arc42 §11 risks: imprecise masks are a high impact risk, mitigated by a correction editor and visual validation. arc42 §14.2 lists mask correction as a decision still to be taken: manual editor in MVP or only re-segmentation.

## Decision

MVP provides automatic re-segmentation on request (trigger a new segmentation for a panel/character), not a manual pixel mask editor. Masks are stored as versioned MaskArtifact artifacts (arc42 §8.2) and can be replaced by re-running segmentation. A manual mask correction editor is deferred to post-MVP, informed by the visual validation experiments.

## Consequences

### Positive

- Smaller MVP scope; no raster/vector editor to build and maintain.
- Versioned masks remain auditable and reproducible.

### Negative

- Users cannot fine-tune a mask by hand in the MVP; they must accept re-segmentation results or adjust attributes/palette instead.

## Related

- arc42 §8.6 Human-in-the-loop.
- arc42 §11 Risks: imprecise masks.
- arc42 §14.2 Pending decision: Mask correction.
