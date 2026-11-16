# ADR-010 — Project scope

**Status:** Proposed (pending product confirmation)

**Deciders:** Architect / Tech Lead, Product

**Date:** 2026-11-15

## Context

arc42 §14.2 lists project scope as a decision still to be taken: a single image, a chapter, or a collection of chapters. arc42 §1.4 non-goals include generating complete chapters with automatic narrative memory. The domain model in arc42 §5.2 and §5.4 distinguishes Project, Page, and Panel, so a Project can contain multiple pages, but the MVP focuses on a single page/image.

## Decision

Initial scope: one image/page per project, with a Project entity that can group multiple pages for future chapter/collection support. Chapter-level or multi-page narrative memory is out of scope for the MVP and deferred to P1+. A project groups pages; a page contains panels; panels contain character detections and masks.

## Consequences

### Positive

- Smaller, testable surface for the MVP.
- Domain model already supports future grouping without schema redesign.

### Negative

- Users wanting to colorize a whole chapter at once must process pages individually in the MVP.

## Related

- arc42 §1.4 Non-goals: chapter generation with narrative memory.
- arc42 §5.2 Backend modules: projects, assets, page_analysis.
- arc42 §14.2 Pending decision: Project scope.
