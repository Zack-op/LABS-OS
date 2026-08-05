# AK Labs OS Release Summary

**Current stable release:** v0.4.3  
**Status:** Production-Calibrated Architecture  
**Validation:** GREEN after PR #2 and PR #3  
**Next milestone:** v0.5.0 Implementer MVP

This document is the permanent engineering handoff for future human engineers
and AI agents. It summarizes the architecture that is implemented and validated
as of v0.4.3.

## Project Vision

AK Labs OS is a persistent AI Engineering Organization. It is designed around
departments, Work Orders, ownership transfer, validation, policy governance,
filesystem safety, and Historian memory.

The system is not a single coding assistant. Code generation is one department
capability inside a larger engineering organization.

## Current Architecture

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

The Orchestrator owns workflow orchestration only. It must not absorb
department authority, engineering state, validation authority, policy
governance, or artifact persistence.

## Completed Milestones

### v0.3.1 - Filesystem Safety

Status: COMPLETE

- Safe Artifact Writer
- traversal blocking
- absolute path blocking
- protected-file blocking
- invalid filename blocking
- duplicate collision handling
- workspace isolation
- policy events for blocked writes
- Historian persistence for blocked filesystem events
- filesystem safety validation suite

### v0.4.x - Handoff-Oriented Intelligence

Status: COMPLETE

- Structured Work Orders
- Persistent Work Orders
- Work Order workspace ownership
- Repository Scanner
- Repository Intelligence
- Repository Profile
- Dependency Graph
- Module Registry
- Alias Registry
- File Selection Engine
- Context Builder
- Engineering Transaction Protocol
- Historian Integration
- Validation Framework
- Artifact Lifecycle
- End-to-End Validation

## Implemented Features

### Work Orders

Work Orders own engineering task state. They include deterministic IDs,
lifecycle state, owner, department, constraints, acceptance criteria,
deliverables, contract fields, status history, and department history.

Canonical identity format:

```text
WO-000001
```

Canonical workspace layout:

```text
output/
  work_orders/
    WO-000001/
```

### Repository Intelligence

Repository Intelligence owns static repository understanding:

- scanner
- repository snapshot
- repository profile
- language and category detection
- repository type inference
- framework and package-manager indicators
- entry points
- dependency graph
- module registry
- alias registry
- metadata indexes

### File Selection

File Selection owns relevant-file reasoning:

- primary files
- supporting files
- reference files
- excluded files
- rule traces
- confidence breakdown
- escalation status and reason

### Context Builder

Context Builder owns `EngineeringContext` packaging. It refuses unresolved
selections, empty primary selections, insufficient confidence, unresolved
escalations, and selected files missing from the repository profile.

### Engineering Transaction Protocol

ETP owns ownership transfer between departments. A transaction records one Work
Order, source department, destination department, transfer intent, evidence,
outcome, and active owner after transfer.

### Reviewer and Verify

Reviewer executes before Verify. Reviewer failure stops the pipeline and
prevents verification execution.

### Historian

Historian owns persistent engineering memory and audit history. It records
events, failures, review evidence, validation evidence, and policy signals. It
does not own workflow authority.

### Policy Engine

Policy Engine owns governance and approval decisions. Policies reference
capabilities rather than provider model IDs.

### Safe Artifact Writer

Safe Artifact Writer owns artifact mutation safety. Unsafe operations are
blocked and recorded instead of silently normalized.

### Release Validation Harness

The validation harness owns independent release validation. It produces
machine-readable JSON, human-readable Markdown, history reports, and
Definition-of-Done results.

## Validation Evidence

v0.4.3 is documented as GREEN after PR #2 and PR #3.

Current registered suites:

- environment
- configuration
- mock_pipeline
- reviewer_regression
- reviewer_adversarial
- architect_normalization
- retry_fallback
- historian
- utf8_artifacts
- verify_gating
- project_context
- filesystem_safety
- work_orders
- etp_integration
- repo_intelligence
- file_selection
- context_builder

Validation commands:

```powershell
python -m validation.cli release --deterministic
python -m validation.cli regression --deterministic
python -m validation.cli adversarial --deterministic
python -m validation.cli dod --deterministic
```

Reports are generated under:

```text
reports/latest.json
reports/latest.md
reports/history/
```

## Engineering Decisions

Accepted decisions are tracked in [docs/DECISIONS.md](docs/DECISIONS.md) and
[docs/ADR/](docs/ADR/).

Key decisions:

- Policies reference capabilities, not model IDs.
- Evidence drives decisions; LLM self-confidence is not a release gate.
- Historian records history but does not govern workflow.
- Reviewer runs before Verify.
- Architect output is strictly validated, retried once, then documented
  fallback is used if still invalid.
- Release Validation Harness is separate from runtime.
- Unsafe artifact paths are rejected, not normalized.
- Duplicate artifacts are deterministically rejected.
- Work Orders own engineering state.
- ETP owns ownership transfer.
- Repository Intelligence owns static repository knowledge.
- File Selection owns relevant-file reasoning.
- Context Builder owns `EngineeringContext` packaging.
- Work Order workspace ownership is canonical.

## Why These Decisions Were Made

AK Labs OS is meant to persist beyond one chat session. The architecture favors
explicit ownership, deterministic identity, validated handoffs, and append-only
evidence because future agents need to continue work without relying on founder
memory or conversation history.

The current boundaries prevent hidden responsibility overlap:

- Orchestrator coordinates but does not own department logic.
- Work Orders describe task state but do not transfer ownership.
- ETP transfers ownership but does not store audit history.
- Historian records audit evidence but does not decide policy.
- Validation proves correctness but does not become runtime execution.
- Safe Artifact Writer mutates artifacts but does not define policy.

## Known Risks

- v0.5.0 Implementer MVP has not been built yet.
- Live provider behavior can still vary and must remain covered by strict
  normalization, retry, and fallback rules.
- Repository Intelligence is static analysis, not semantic repository
  understanding.
- File Selection depends on rule coverage and must escalate when confidence is
  insufficient.
- Documentation must be kept synchronized with validation results after future
  releases.

## Migration Strategy

Future work should migrate implementation execution onto the v0.4.3 contracts
without redesigning them:

1. Accept a Work Order.
2. Build Repository Profile.
3. Run File Selection.
4. Build EngineeringContext.
5. Execute Implementer inside the Work Order workspace.
6. Write artifacts through Safe Artifact Writer.
7. Transfer ownership through ETP.
8. Persist evidence in Historian.
9. Enforce Reviewer and Verify gates.
10. Prove behavior through release validation.

## Next Roadmap

Only one next milestone is approved:

### v0.5.0 - Implementer MVP

Objective: introduce the minimum viable Implementer capability without changing
the v0.4.3 architecture.

Expected constraints:

- consume `EngineeringContext`
- operate inside `output/work_orders/<work_order_id>/`
- write only through Safe Artifact Writer
- preserve Reviewer before Verify
- emit Historian evidence
- respect Policy Engine governance
- use ETP for ownership transfer

## Definition of Done for v0.5.0

- Implementer accepts a Work Order and EngineeringContext.
- Implementer writes artifacts only through Safe Artifact Writer.
- Implementer output remains inside the Work Order workspace.
- Reviewer failure prevents Verify execution.
- Historian records Implementer outputs and failures.
- ETP transfer evidence references Implementer outputs.
- Validation includes focused Implementer MVP suites.
- `release`, `regression`, `adversarial`, and `dod` pass in deterministic mode.

## Documentation Entry Points

- [START_HERE.md](START_HERE.md)
- [README.md](README.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/ENGINEERING_GUIDE.md](docs/ENGINEERING_GUIDE.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)
- [docs/DECISIONS.md](docs/DECISIONS.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [docs/validation.md](docs/validation.md)
- [CHANGELOG.md](CHANGELOG.md)
- [PROJECT_STATUS.md](PROJECT_STATUS.md)
- [RELEASE_NOTES_v0.4.3.md](RELEASE_NOTES_v0.4.3.md)
