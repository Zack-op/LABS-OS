# AK Labs OS Architecture

Canonical onboarding docs:
[START_HERE.md](../START_HERE.md),
[ENGINEERING_GUIDE.md](ENGINEERING_GUIDE.md),
[ROADMAP.md](ROADMAP.md),
[CONTRIBUTING.md](CONTRIBUTING.md),
[DECISIONS.md](DECISIONS.md).

## Purpose

AK Labs OS is being built as a persistent AI Engineering Organization. The
current system is still an MVP, but it already contains the foundations of an
engineering organization:

- departments with distinct responsibilities
- policy-governed execution
- blocking review and validation gates
- organizational memory
- release validation infrastructure
- filesystem safety
- structured Work Order domain contracts

The system is not yet repository-aware. It does not scan arbitrary repositories,
select files, implement multi-file plans, or manage Git commits.

## Current Runtime Flow

Implemented runtime flow in `orchestrator.py`:

```text
User Request
    |
    v
Architect
    |
    v
Developer
    |
    v
Reviewer
    |
    v
Verify
    |
    v
Commit Message
    |
    v
PROJECT_CONTEXT.md + Historian / policy logs
```

The v0.4.1 Work Order domain model exists, but the runtime pipeline does not
yet require Work Orders as the handoff format between departments.

Planned v0.4.2 architecture introduces the Engineering Transaction Protocol
(ETP) as Department Handoff Infrastructure. ETP is not implemented in this
sprint and must not be treated as runtime behavior until a later implementation
milestone adds it.

## Major Subsystems

### Orchestrator

File: `orchestrator.py`

Responsibilities:

- coordinate the current single-request pipeline
- call Architect, Developer, Reviewer, Verify, and commit-message generation
- stop when a blocking policy gate escalates
- append shipped, failed, blocked, or escalated outcomes to `PROJECT_CONTEXT.md`

Implemented:

- mock mode
- live model calls through `llm_router.py`
- strict Architect work-order-like JSON parsing with retry and fallback
- Developer generation of a single Python artifact
- Reviewer before Verify
- UTF-8 artifact and context handling
- Safe Artifact Writer integration for project artifact writes

Not implemented:

- repository intelligence
- multi-file planning
- real Git branch or commit operations
- mandatory Work Order handoff between departments

### Departments

Departments are currently implemented as functions inside `orchestrator.py`.

Architect:

- turns a loose feature request into a bounded structured brief
- enforces strict JSON schema for current runtime briefs
- retries once on malformed output
- uses deterministic fallback after repeated malformed output

Developer:

- generates a single self-contained Python module
- writes through `SafeArtifactWriter`

Reviewer:

- executes after Developer and before Verify
- reads Architect output, Developer result, and generated files
- returns structured review JSON
- blocks plaintext passwords, missing authentication, SQL injection, command
  execution, dangerous filesystem operations, and critical architecture
  violations

Verify:

- checks that output exists, is non-empty, and parses as Python
- does not replace real test execution

Commit Message:

- generates a conventional-commit-style summary
- does not create a Git commit

### Policy Engine

File: `policy_engine.py`

Responsibilities:

- load `policies.yaml`
- evaluate policy facts
- return proceed/escalate decisions
- include `interrupt_level`
- log every decision to SQLite `policy_log`

Implemented interrupt levels:

- `none`
- `review`
- `approval`
- `emergency`

Limitations:

- approval flow is data only
- no approval queue or continuation dispatcher exists yet

### Capability Routing

Files: `capabilities.yaml`, `capability_router.py`, `llm_router.py`

Responsibilities:

- keep provider/model names out of policy definitions
- resolve abstract capabilities such as `coding_fast`
- route model calls to supported providers

Implemented:

- capability to provider/model resolution
- mock mode
- Groq live mode
- Claude path is present as an intended provider route, dependent on key and
  future wiring

Architectural rule:

- policies reference capabilities, never model IDs

### Historian

File: `historian.py`

Responsibilities:

- compute policy statistics from `policy_log`
- detect repeated escalations
- create pending policy candidates
- persist Reviewer results
- persist blocked filesystem events

Implemented storage:

- `policy_candidates`
- `engineering_reviews`
- `filesystem_events`

Limitations:

- Historian is not yet a full organizational knowledge graph
- it does not automatically rewrite policies
- it does not yet attach every future artifact to a durable Work Order ID

### Safe Artifact Writer and Filesystem Safety

File: `safe_artifact_writer.py`

Responsibilities:

- centralize runtime project-artifact mutation
- reject unsafe paths before filesystem mutation
- call the `filesystem_safety` policy on blocked writes
- record blocked filesystem events through Historian

Implemented protections:

- path traversal rejection
- absolute path rejection
- workspace escape rejection
- reserved filename rejection
- invalid filename character rejection
- duplicate artifact collision rejection
- protected project-file write rejection unless explicitly authorized
- symlink escape checks where supported by the local filesystem

Design rule:

- unsafe paths are rejected, not silently normalized

### Work Orders

Package: `work_orders/`

Responsibilities:

- define the canonical structured engineering contract
- provide deterministic IDs
- define lifecycle transitions
- validate required fields and enum values
- serialize to/from JSON
- track status and department history

Implemented:

- schema version `1`
- IDs like `WO-000001`
- priority: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`
- complexity: `XS`, `S`, `M`, `L`, `XL`
- risk: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- structured acceptance criteria
- deliverables
- constraints
- Work Order Contract: `inputs`, `outputs`, `preconditions`,
  `postconditions`

Not implemented:

- mandatory runtime use
- durable persistence for Work Orders
- repository intelligence or file selection

### Engineering Transaction Protocol

Planned subsystem for v0.4.2.

Purpose:

- make department handoffs explicit, deterministic, auditable ownership
  transfers
- keep Work Orders as the canonical engineering state
- prevent departments from mutating ownership informally

Responsibilities:

- transfer a Work Order from one department to another
- record source department, destination department, owner, status intent, and
  handoff rationale
- define the minimum transaction envelope required for department handoff
- preserve backward compatibility with the current runtime until integration is
  explicitly implemented

Relationship with Work Orders:

- Work Orders remain the canonical engineering object
- ETP does not own Work Order schema, acceptance criteria, deliverables,
  constraints, or contract fields
- ETP only owns the act of transferring responsibility for a Work Order

Relationship with Historian:

- Historian remains the canonical audit system
- ETP should emit auditable transfer records to Historian when implemented
- Historian should store transfer evidence, not decide whether a transfer is
  allowed

Relationship with Validation:

- the Release Validation Harness remains the canonical validation authority
- ETP implementation must add validation proving deterministic transitions,
  invalid transfer rejection, auditability, and backward compatibility
- validation results are not owned by ETP

Future extensibility:

- ETP can later support repository-aware departments, approval queues, and
  context packets without changing Work Order ownership
- extensions must keep ownership transfer separate from engineering state,
  historical audit, and validation authority

Decision reference:

- [ADR-0012: Separate Work Order State from Department Transfer Behavior](DECISIONS.md#adr-0012-separate-work-order-state-from-department-transfer-behavior)

### Canonical Ownership Invariant

Every engineering concern must have exactly one canonical owner. Other
subsystems may reference, validate, persist, or report on that concern, but
they must not become competing sources of truth.

| Engineering concern | Canonical owner | Status |
|---|---|---|
| Engineering state | Work Orders | Implemented domain model |
| Ownership transfer | Engineering Transaction Protocol | Planned v0.4.2 |
| Historical record | Historian | Implemented foundation |
| Validation results | Validation Harness | Implemented |
| Policy enforcement | Policy Engine | Implemented |
| Artifact persistence | Safe Artifact Writer | Implemented |
| Repository knowledge | Repository Intelligence | Planned |
| Context construction | Context Builder | Planned |

Duplicate ownership is prohibited because it creates ambiguous authority. If
two subsystems both own the same concern, future agents will not know which
record to trust, validation cannot define a single source of truth, and
Historian cannot reconstruct the lifecycle reliably.

### Release Validation Harness

Package: `validation/`

Reporters: `reporters/`

Responsibilities:

- execute deterministic release gates
- run regression and adversarial checks
- produce machine-readable JSON and human-readable Markdown
- update `RELEASE_SUMMARY.md`
- enforce Definition of Done

Commands:

```bash
python -m validation.cli release --deterministic
python -m validation.cli regression --deterministic
python -m validation.cli adversarial --deterministic
python -m validation.cli dod --deterministic
```

Current required release suites:

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

### Reports and Release Summary

Reports are written under `reports/`.

- `reports/latest.json`
- `reports/latest.md`
- `reports/history/*.json`
- `reports/history/*.md`

`RELEASE_SUMMARY.md` is the long-lived engineering handoff. It records release
validation results, implemented milestones, known risks, decisions, and next
roadmap.

## Repository Layout

```text
.
├── START_HERE.md
├── README.md
├── ARCHITECTURE.md
├── RELEASE_SUMMARY.md
├── docs/
├── orchestrator.py
├── policy_engine.py
├── historian.py
├── safe_artifact_writer.py
├── capability_router.py
├── llm_router.py
├── dev_tools.py
├── policies.yaml
├── capabilities.yaml
├── culture.yaml
├── work_orders/
├── validation/
├── reporters/
└── reports/
```

## Data Stores and Generated Artifacts

Runtime-generated artifacts:

- `output/` generated code and review artifacts
- `PROJECT_CONTEXT.md` appended run history
- `ak_labs_os.db` SQLite runtime memory

Validation-generated artifacts:

- `reports/`
- isolated temporary validation workspaces

## Implemented vs Planned

Implemented:

- policy evaluation and logging
- mock and live model routing foundation
- Architect normalization, retry, and fallback
- Developer single-file generation
- Reviewer blocking gate
- Verify syntax/existence gate
- Historian event persistence
- Safe Artifact Writer
- Release Validation Harness
- Work Order Domain Model

Planned:

- mandatory Work Order handoff between departments
- Engineering Transaction Protocol as Department Handoff Infrastructure
- durable Work Order persistence
- repository intelligence
- context builder
- real test execution
- Git branch, commit, and release automation
- approval queue and continuation workflow
