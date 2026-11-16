# ADR-012 — Initial AI model baseline

**Status:** Proposed (pending model benchmark and license audit)

**Deciders:** ML Engineer, Architect / Tech Lead

**Date:** 2026-11-15

## Context

arc42 §1.4 non-goals include training a foundation model from scratch and guaranteeing exact reconstruction of unknown official colors. arc42 §2.1 constraint 9: training data must have compatible licenses. arc42 §8.4: the model registry records name, family, version/checkpoint, weights hash, license and source, capabilities, hardware requirements, supported parameters, and status. arc42 §14.2 lists the initial model (baseline to reproduce and usage license) as a decision still to be taken, validated by comparative evaluation on a fixed set.

## Decision

No concrete model is frozen in P0. The initial baseline will be selected after a reproducible comparative evaluation on a fixed, licensed test set, using the model registry to record the chosen model's name, family, checkpoint, weights hash, license, and source. Models integrate through adapters (ADR-004) so the baseline can be replaced without changing use cases. All models must have documented, compatible licenses and provenance.

## Consequences

### Positive

- Baseline decision is evidence-driven, not assumed.
- Adapter-based integration keeps the baseline replaceable.
- License and provenance are recorded before any model is used.

### Negative

- No baseline is available in P0; colorization quality cannot be measured until the benchmark completes.

## Related

- ADR-004: Decoupled AI engine through interfaces.
- ADR-007: Independent adapters for detection, identity, and colorization.
- arc42 §8.4 Model versioning.
- arc42 §14.2 Pending decision: Initial model.
