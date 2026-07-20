# Roadmap

This roadmap distinguishes implemented functionality from planned milestones.
For current release evidence, see [RELEASE_SUMMARY.md](../RELEASE_SUMMARY.md).
For architecture, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Current Release State

Current suggested version: `v0.4.1-alpha`.

Release validation status:

- `release`: PASS
- `regression`: PASS
- `adversarial`: PASS
- `dod`: PASS

The release harness currently reports 100/100 readiness for the implemented
v0.4.1 gates.

## Completed Milestones

### v0.1 - Policy-Governed MVP Foundation

Implemented:

- standalone Python pipeline
- YAML policies
- SQLite policy log
- mock mode
- capability routing foundation

### v0.2 - Historian and Governance Substrate

Implemented:

- policy statistics
- repeated escalation detection
- pending policy candidates
- human decision recording
- initial organizational culture file

### v0.3 - Reviewer, Fallback, and Release Validation

Implemented:

- Reviewer stage before Verify
- structured Reviewer output
- insecure-code blocking
- Architect normalization and retry/fallback behavior
- UTF-8 artifact handling
- verify gating regression coverage
- Release Validation Harness
- JSON and Markdown reports
- Definition of Done engine

### v0.3.1 - Filesystem Safety

Implemented:

- Safe Artifact Writer
- filesystem safety policy
- Historian persistence for blocked filesystem events
- rejection of unsafe paths and duplicate collisions
- reproducible configuration gates

### v0.4.1 - Work Order Domain Model

Implemented:

- `work_orders/` package
- schema version `1`
- deterministic IDs
- lifecycle transitions
- priority, complexity, and risk enums
- structured acceptance criteria
- deliverables
- constraints
- department ownership history
- status history
- Work Order Contract
- JSON serialization
- validation suite

Not implemented in v0.4.1:

- mandatory Work Order runtime handoff
- Work Order persistence
- repository intelligence
- context builder
- implementer or planning AI

## Next Milestone: v0.4.2 - Engineering Transaction Protocol

Department Handoff Infrastructure

Goal: define the Engineering Transaction Protocol (ETP) as the canonical
ownership-transfer mechanism between departments.

The Work Order remains the canonical engineering object. ETP owns transfer
behavior only. Historian remains the canonical audit system. The Validation
Harness remains the canonical validation authority.

Scope:

- define the ETP transaction envelope
- define deterministic department transfer semantics
- define valid source and destination department rules
- define how transfer attempts are recorded for Historian
- define validation gates for successful and rejected transfers
- preserve current runtime behavior until an implementation milestone changes it

Expected deliverables:

- ETP specification
- ETP validation plan
- ADR references and documentation updates
- specification-ready handoff for v0.4.2B

Documentation-only reconciliation scope:

- v0.4.2A freezes architecture before implementation
- no runtime code changes
- no validation code changes
- no Work Order schema changes

Explicit non-goals:

- changing Work Order schema or lifecycle
- making Work Orders mandatory in runtime during v0.4.2A
- repository scanner
- file selection engine
- Git automation
- multi-file implementation planning
- execution AI expansion
- approval queue implementation
- Historian redesign

## Future Milestones

### Repository Intelligence

Planned:

- repository scanning
- component discovery
- dependency/context map
- file selection assistance

Prerequisite:

- Work Orders must already be mandatory department contracts.

### Context Builder

Planned:

- build task-specific context packets
- use Historian and repository intelligence
- attach context to Work Orders

### Real Validation and Tests

Planned:

- replace syntax-only Verify with test execution
- connect `run_tests_on_commit`
- record validation results in Historian

### Durable Approval Workflow

Planned:

- approval queue
- blocking continuation state
- resumable policy decisions

### Git and Release Automation

Planned:

- feature branch creation
- commits
- tagged releases
- release notes

## Deferred By Design

Deferred until evidence justifies them:

- LLM self-confidence scores
- autonomous policy edits
- policy inheritance
- repository-wide implementation without Work Orders
- hidden prompt-based coordination between departments
