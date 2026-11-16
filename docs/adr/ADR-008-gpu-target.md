# ADR-008 — GPU target for local inference

**Status:** Proposed (pending hardware benchmark validation)

**Deciders:** Architect / Tech Lead, ML Engineer

**Date:** 2026-11-15

## Context

arc42 §2.1 technical constraints require inference to use NVIDIA/CUDA GPU when available, without assuming a GPU always exists, and to limit GPU tasks to avoid concurrent loads exceeding VRAM. arc42 §7.4 states the GPU worker must validate drivers, CUDA, PyTorch, and container runtime compatibility before running, and may run on the host connected to the local broker if container GPU support complicates the environment. arc42 §14.2 lists the GPU target (exact model, VRAM, CUDA compatibility) as a decision still to be taken, to be validated with benchmarks at the target resolution.

## Decision

Target NVIDIA GPUs with CUDA as the primary local inference device for the GPU worker. The architecture does not assume a GPU is always present: CPU-only operation remains supported for non-GPU tasks. The GPU worker validates the driver/CUDA/PyTorch/container-runtime combination at startup; if container GPU support is problematic, the GPU worker runs on the host and connects to the local Redis broker. A single GPU worker process with effective concurrency of 1 is used initially for large models (see ADR-006).

## Consequences

### Positive

- Clear hardware target for benchmarking and VRAM sizing.
- Graceful degradation when no GPU is available.
- Predictable memory usage through single-worker, concurrency-limited GPU execution.

### Negative

- Performance depends on the validated GPU model; under-specified hardware may be too slow for large generative models.
- Container GPU setup adds environment complexity; the host fallback is a mitigation, not a long-term multi-machine solution.

## Related

- ADR-006: Single GPU worker initially.
- arc42 §7.4 GPU compatibility.
- arc42 §14.2 Pending decision: GPU target.
