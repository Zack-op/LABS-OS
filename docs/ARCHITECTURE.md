# Architecture Guide

This document is the operational companion to the canonical architecture freeze
in [../ARCHITECTURE.md](../ARCHITECTURE.md). If the two disagree, update this
file to match the root architecture document.

**Current stable release:** v0.4.3  
**Status:** Architecture Freeze  
**Next milestone:** v0.5.0 Implementer MVP

## System Shape

AK Labs OS is a persistent AI Engineering Organization. It coordinates work
through departments and structured handoffs instead of passing natural-language
prompts directly between all stages.

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

## Department Responsibilities

| Department or Subsystem | Responsibility |
|---|---|
| Architect | Converts user intent into structured engineering direction. |
| Repository Intelligence | Builds repository snapshots, profiles, dependency metadata, module indexes, and aliases. |
| File Selection | Produces evidence-backed relevant-file selections and escalates insufficient evidence. |
| Context Builder | Packages validated inputs into `EngineeringContext`. |
| Developer | Generates implementation artifacts. |
| Reviewer | Performs engineering and security review before verification. |
| Verify | Runs executable verification after Reviewer approval. |
| Historian | Persists engineering memory, audit history, failures, and evidence. |

## Platform Responsibilities

| Platform Subsystem | Responsibility |
|---|---|
| Work Orders | Canonical engineering state, lifecycle, contract, acceptance criteria, deliverables, and ID. |
| Engineering Transaction Protocol | Deterministic ownership transfer between departments. |
| Policy Engine | Governance evaluation and policy events. |
| Safe Artifact Writer | Approved artifact mutation and filesystem safety. |
| Validation Harness | Independent release validation, reports, and Definition of Done. |
| Orchestrator | Workflow orchestration only. |

## Repository Intelligence Boundary

Repository Intelligence owns static repository knowledge:

- scanning
- profiling
- dependency graph
- module registry
- alias registry
- repository metadata
- category, language, framework, and entry-point indexes

It does not decide what to edit and does not package implementation context.

## File Selection Boundary

File Selection owns engineering reasoning about relevant files:

- primary files
- supporting files
- reference files
- exclusions
- rule traces
- confidence breakdown
- escalation reason

It does not scan the repository or mutate artifacts.

## Context Builder Boundary

Context Builder owns `EngineeringContext` packaging. It validates that the file
selection is resolved and that selected files exist in the repository profile
before creating context for implementation.

## Work Order Boundary

Work Orders own engineering task state. The canonical workspace layout is:

```text
output/
  work_orders/
    WO-000001/
```

Work Orders do not own department-transfer behavior. ETP owns that boundary.

## Handoff Boundary

ETP records ownership transfer. A transaction has one Work Order, source
department, destination department, evidence package, outcome, and active owner
after transfer.

ETP does not replace Historian, Validation Harness, Policy Engine, Safe
Artifact Writer, or Work Orders.

## Safety Boundary

Safe Artifact Writer is the approved mutation layer for artifacts. It blocks
unsafe paths, protected-file writes, duplicate collisions, invalid filenames,
and workspace escapes. It rejects unsafe operations instead of repairing them.

## Validation Boundary

The Release Validation Harness validates the organization from outside the
runtime pipeline. It produces:

- `reports/latest.json`
- `reports/latest.md`
- `reports/history/`

The harness must remain independent from runtime execution.

## Extension Rule

New departments must define:

- owned responsibility
- required inputs
- produced outputs
- evidence requirements
- validation expectations
- Historian records
- policy touchpoints

They must integrate without moving ownership away from the frozen v0.4.3
subsystems.
