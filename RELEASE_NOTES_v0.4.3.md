# Release Notes - v0.4.3

## Summary

AK Labs OS v0.4.3 freezes the Production-Calibrated Architecture after the
repository intelligence and handoff stabilization work. The release documents
the completed Handoff-Oriented Intelligence layer and sets v0.5.0 Implementer
MVP as the next milestone.

## New Capabilities

- Repository Scanner
- Repository Intelligence
- Repository Profile
- Dependency Graph
- Module Registry
- Alias Registry
- Structured Work Orders
- Persistent Work Orders
- Work Order workspace ownership
- File Selection Engine
- Context Builder
- Engineering Transaction Protocol integration
- Engineering Context packaging
- Validation coverage for Repository Intelligence, File Selection, Context
  Builder, Work Orders, and ETP integration

## Architecture Stabilization

v0.4.3 freezes subsystem ownership:

- Repository Intelligence owns scanning, profiling, dependency graph, metadata,
  module registry, and alias registry.
- File Selection owns engineering reasoning, evidence generation, confidence,
  and escalation.
- Context Builder owns `EngineeringContext` packaging.
- Developer owns implementation generation.
- Reviewer owns engineering review.
- Historian owns persistent engineering memory.
- Orchestrator owns workflow orchestration only.

The canonical Work Order artifact layout is:

```text
output/
  work_orders/
    WO-000001/
```

## Validation Campaign

The v0.4.3 validation campaign is documented as GREEN after PR #2 and PR #3.
The release gate includes:

- environment
- configuration
- mock pipeline
- reviewer regression
- reviewer adversarial
- architect normalization
- retry fallback
- historian
- UTF-8 artifacts
- verify gating
- project context
- filesystem safety
- Work Orders
- ETP integration
- Repository Intelligence
- File Selection
- Context Builder

## Production Readiness

This release is production-calibrated for architecture and release discipline.
It is not a claim that future code generation quality is complete. The system
has the organizational contracts required for the next implementation milestone.

## Migration Notes

- New contributors should start with `START_HERE.md`.
- Architecture decisions should follow `ARCHITECTURE.md` and `docs/DECISIONS.md`.
- New artifacts should use the Work Order workspace model.
- Future implementation must preserve Safe Artifact Writer, Policy Engine,
  Historian, ETP, and validation boundaries.

## Next Milestone

v0.5.0 Implementer MVP.

The Implementer MVP should consume `EngineeringContext`, operate inside the Work
Order workspace model, write through Safe Artifact Writer, preserve Reviewer and
Verify gates, and emit Historian evidence.
