# AK Labs OS Architecture

**Canonical architecture reference:** v0.4.3  
**Status:** Architecture Freeze  
**Next milestone:** v0.5.0 Implementer MVP

This document freezes subsystem ownership for AK Labs OS. Future work may
extend the system, but it must not silently move responsibilities between
subsystems.

## Vision

AK Labs OS is a persistent AI Engineering Organization. It is organized around
departments, structured Work Orders, deterministic handoffs, validation,
historical memory, policy governance, and safe artifact handling.

Coding is one department capability. The architecture exists to make
engineering work auditable, repeatable, and reviewable across sessions.

## Current Pipeline

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

The Orchestrator coordinates the workflow. It does not own the internal
authority of the departments it invokes.

## Frozen Ownership Boundaries

| Subsystem | Owns | Does Not Own |
|---|---|---|
| Architect | Structured engineering direction from user intent | Repository scanning, code generation, validation |
| Work Orders | Engineering state, lifecycle, contract, acceptance criteria, deliverables, persistent ID | Ownership-transfer mechanics, repository analysis |
| Repository Intelligence | Scanning, profiling, dependency graph, module registry, alias registry, repository metadata | File-selection decisions, implementation choices |
| File Selection | Engineering reasoning about relevant files, evidence generation, confidence, escalation | Repository scanning, context packaging, code edits |
| Context Builder | `EngineeringContext` packaging from Work Order, repository profile, and file selection | Repository scanning, selection rules, implementation |
| Developer | Implementation generation | Review authority, verification authority, artifact safety policy |
| Reviewer | Engineering review, security review, failure findings | Executable verification, policy ownership |
| Verify | Executable verification after Reviewer approval | Security review, architecture approval |
| Historian | Persistent engineering memory, audit history, failure evidence | Workflow authority, validation authority, policy decisions |
| Policy Engine | Governance evaluation, approval flow, policy events | Model routing, artifact persistence, validation results |
| Safe Artifact Writer | Approved create, modify, rename, and delete operations for artifacts | Work Order identity, policy definition, Historian storage design |
| Engineering Transaction Protocol | Deterministic ownership transfer between departments | Work Order state, audit storage, validation correctness |
| Validation Harness | Independent release validation, DoD gates, reports | Runtime orchestration or production execution |
| Orchestrator | Workflow orchestration only | Department ownership, engineering state, policy decisions, historical memory |

## Core Contracts

### Work Orders

Work Orders are the canonical engineering state object. They include:

- deterministic ID such as `WO-000001`
- title, objective, description, priority, risk, complexity
- lifecycle status
- current owner and department
- acceptance criteria
- deliverables
- constraints and affected components
- contract inputs, outputs, preconditions, and postconditions
- status and department history

Work Orders are persisted under the canonical workspace layout:

```text
output/
  work_orders/
    WO-000001/
```

### Repository Intelligence

Repository Intelligence builds a static repository profile. It owns:

- file and directory scanning
- language and category detection
- repository type inference
- framework and package-manager indicators
- entry-point detection
- dependency graph
- runtime dependency index
- module-to-file registry
- file-to-module registry
- alias registry
- centrality metadata

It does not decide what should be edited. That belongs to File Selection.

### File Selection

File Selection converts Work Order intent plus repository metadata into an
evidence-backed selection. It owns:

- primary files
- supporting files
- reference files
- excluded files
- rule traces
- confidence breakdown
- escalation status and reason

Selections with no primary files, unresolved conflicts, or low rule coverage
must escalate instead of being packaged as usable engineering context.

### Context Builder

Context Builder packages the validated engineering inputs into
`EngineeringContext`. It refuses unresolved file selections and missing selected
files. Its output is the controlled context passed toward implementation.

### Engineering Transaction Protocol

ETP owns ownership transfer only. It records deterministic transaction records
with one Work Order, one source department, one destination department,
evidence, outcome, and active owner after transfer.

ETP does not own Work Order state, Historian persistence, validation
correctness, policy governance, or artifact persistence.

### Reviewer and Verify

Reviewer runs before Verify. Reviewer failure stops the pipeline and prevents
verification execution. Verify is allowed only after Reviewer approval.

### Safe Artifact Writer

All approved artifact mutation flows through Safe Artifact Writer. Unsafe paths
are rejected, not repaired. Protected files require explicit authorization.
Duplicate artifact collisions are deterministic failures unless a milestone
explicitly changes the collision policy.

### Historian

Historian owns persistent engineering memory and audit evidence. It records
events, failures, policy signals, reviews, and release evidence. It does not
make workflow decisions.

### Validation Harness

The validation harness lives outside runtime. It validates the organization,
writes JSON and Markdown reports, and enforces the Definition of Done. It must
not become a runtime dependency.

## Deterministic Invariants

- Policies reference capabilities, not model IDs.
- Work Order IDs are deterministic and sequential.
- Exactly one department owns a Work Order at each transfer point.
- Transaction history is append-only and replayable.
- Accepted evidence is immutable.
- Unsafe filesystem paths are rejected rather than normalized.
- Validation reports are machine-readable and human-readable.
- The Orchestrator coordinates only; it does not absorb department ownership.

## Extension Rule

Future departments may be added only by defining their ownership boundary,
inputs, outputs, validation expectations, and Historian evidence. They must
integrate through Work Orders, ETP, Policy Engine, Validation Harness, and Safe
Artifact Writer without redefining those systems.
