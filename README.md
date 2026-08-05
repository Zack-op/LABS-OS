# AK Labs OS

**Version:** v0.4.3  
**Status:** Production-Calibrated Architecture  
**Next milestone:** v0.5.0 Implementer MVP

AK Labs OS is a persistent AI Engineering Organization. It coordinates
engineering work through structured departments, Work Orders, policy gates,
validation, historical memory, safe artifact handling, and deterministic
handoffs.

The goal is not to create a more convenient coding prompt. The goal is to build
an autonomous engineering organization whose work can be validated, audited,
replayed, and extended without losing architectural intent.

## High-Level Architecture

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

The Orchestrator coordinates this pipeline. Department responsibilities are
owned by their subsystem contracts, not by prompt text.

## Current Capabilities

- Structured Architect output with retry and deterministic fallback.
- Repository Scanner and Repository Intelligence profile generation.
- Dependency graph, module registry, alias registry, and repository metadata.
- Structured Work Order domain model with deterministic IDs.
- Persistent Work Order identity and canonical workspace layout.
- File Selection Engine with rule traces, confidence breakdown, and escalation.
- Context Builder that packages validated `EngineeringContext` objects.
- Developer stage for implementation generation.
- Reviewer gate before verification, including adversarial security checks.
- Verification gate that does not execute after Reviewer failure.
- Historian persistence for engineering memory and failure evidence.
- Policy Engine with capability-based governance.
- Safe Artifact Writer for protected, deterministic filesystem operations.
- Release Validation Harness with JSON, Markdown, regression, adversarial, and
  DoD outputs.
- Engineering Transaction Protocol for ownership transfer between departments.

## Deterministic Design Principles

- Use stable Work Order IDs such as `WO-000001`.
- Avoid UUIDs, timestamps, and randomness for durable engineering identity.
- Reject unsafe filesystem paths instead of repairing them.
- Keep policy rules independent of model IDs.
- Require structured evidence for ownership transfer and validation.
- Persist audit history append-only.
- Keep validation separate from runtime execution.
- Preserve exactly one canonical owner for every engineering concern.

## Canonical Ownership

| Subsystem | Owns |
|---|---|
| Work Orders | Engineering task state, lifecycle, contracts, acceptance criteria |
| Repository Intelligence | Scanning, profiling, dependency graph, metadata, indexes |
| File Selection | File reasoning, evidence generation, confidence, escalation |
| Context Builder | `EngineeringContext` packaging |
| Developer | Implementation generation |
| Reviewer | Engineering and security review |
| Verify | Executable verification after Reviewer approval |
| Historian | Persistent engineering memory and audit history |
| Policy Engine | Governance and approval decisions |
| Safe Artifact Writer | Artifact mutation and filesystem safety |
| ETP | Department ownership transfer |
| Orchestrator | Workflow orchestration only |

See [ARCHITECTURE.md](ARCHITECTURE.md) for the frozen ownership reference.

## Repository Layout

```text
ARCHITECTURE.md                 canonical architecture freeze
START_HERE.md                   first-read guide for engineers and AI agents
README.md                       project overview
orchestrator.py                 workflow coordination
policy_engine.py                policy evaluation
safe_artifact_writer.py         filesystem safety enforcement
historian.py                    persistent engineering memory
capability_router.py            capability routing
llm_router.py                   provider and mock execution routing

repository_intelligence/        scanner, profile, dependency graph, indexes
file_selection/                 selection rules, traces, escalation
context_builder/                EngineeringContext builder
work_orders/                    Work Order model, IDs, lifecycle, persistence
etp/                            ownership-transfer protocol
validation/                     release validation harness and suites
reporters/                      report writers and release-summary updates
reports/                        generated validation evidence
docs/                           engineering documentation and ADRs
handoffs/                       ETP specification documents
output/
  work_orders/
    WO-000001/                  canonical Work Order workspace layout
```

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

Mock execution:

```powershell
python orchestrator.py "Build a function that validates an email address" --mock
```

Release validation:

```powershell
python -m validation.cli release --deterministic
python -m validation.cli regression --deterministic
python -m validation.cli adversarial --deterministic
python -m validation.cli dod --deterministic
```

## Validation Status

v0.4.3 is GREEN under the release validation campaign after PR #2 and PR #3.
The validation registry includes environment, configuration, mock pipeline,
Reviewer regression, Reviewer adversarial, Architect normalization,
retry/fallback, Historian, UTF-8 artifacts, verify gating, project context,
filesystem safety, Work Orders, ETP integration, Repository Intelligence, File
Selection, and Context Builder.

Generated reports live in:

```text
reports/latest.json
reports/latest.md
reports/history/
```

## Roadmap

Completed:

- v0.3.1 Filesystem Safety
- v0.4.x Handoff-Oriented Intelligence

Next:

- v0.5.0 Implementer MVP

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Contributor Entry Points

- Start with [START_HERE.md](START_HERE.md).
- Read [docs/ENGINEERING_GUIDE.md](docs/ENGINEERING_GUIDE.md) before editing.
- Read [docs/DECISIONS.md](docs/DECISIONS.md) before changing architecture.
- Read [docs/validation.md](docs/validation.md) before changing validation or
  release gates.

Architecture must be preserved unless the active milestone explicitly requires
change.
