# Roadmap

**Current stable release:** v0.4.3  
**Current status:** Production-Calibrated Architecture  
**Next milestone:** v0.5.0 Implementer MVP

This roadmap records implemented milestones and the single approved next
milestone. It does not describe speculative future capabilities.

## Completed Milestones

### v0.3.1

████████████████████

**Filesystem Safety**

**Status:** COMPLETE

Completed work:

- Safe Artifact Writer
- centralized artifact writes
- traversal blocking
- absolute path blocking
- invalid and reserved filename blocking
- protected-file blocking
- duplicate collision handling
- workspace isolation enforcement
- policy events for blocked filesystem operations
- Historian persistence for blocked filesystem events
- validation suite coverage for filesystem safety

### v0.4.x

████████████████████

**Handoff-Oriented Intelligence**

**Status:** COMPLETE

Completed work:

- Repository Scanner
- Repository Intelligence
- Structured Work Orders
- Persistent Work Orders
- Repository Profile
- Dependency Graph
- Module Registry
- Alias Registry
- File Selection Engine
- Context Builder
- Engineering Transaction Protocol
- Historian Integration
- Validation Framework
- Workspace Ownership
- Artifact Lifecycle
- End-to-End Validation

## Current Architecture

The v0.4.3 architecture is frozen around this pipeline:

```text
Architect
  |
Repository Intelligence
  |
File Selection
  |
Context Builder
  |
Developer
  |
Reviewer
  |
Verify
  |
Historian
```

The canonical Work Order workspace layout is:

```text
output/
  work_orders/
    WO-000001/
```

## Next Milestone

### v0.5.0 - Implementer MVP

**Objective:** introduce the minimum viable Implementer capability without
redesigning the v0.4.3 architecture.

Expected focus:

- consume `EngineeringContext`
- operate within the Work Order workspace model
- use Safe Artifact Writer for artifact mutation
- preserve Reviewer and Verify gates
- emit Historian evidence
- respect Policy Engine decisions
- preserve deterministic ownership transfer through ETP

Definition of Done for v0.5.0:

- Implementer accepts a Work Order and EngineeringContext.
- Implementer writes only through Safe Artifact Writer.
- Implementer output remains inside `output/work_orders/<work_order_id>/`.
- Reviewer failure still prevents Verify execution.
- Validation includes focused Implementer MVP regression coverage.
- Release validation remains GREEN.

No later milestones are approved in this roadmap.
