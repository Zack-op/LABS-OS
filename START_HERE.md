# START HERE - AK Labs OS

**Current stable release:** v0.4.3  
**Status:** Production-Calibrated Architecture  
**Next milestone:** v0.5.0 Implementer MVP

This file is the first document future human engineers and AI engineering
agents should read after cloning the repository.

## What AK Labs OS Is

AK Labs OS is a persistent AI Engineering Organization. It is not a single
coding assistant. The system is organized as departments with explicit
contracts, validation gates, policy enforcement, persistent memory, and
controlled artifact handling.

The current architecture is frozen at v0.4.3 after the repository intelligence,
handoff, context, ownership, and validation stabilization work.

## Current Engineering Pipeline

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

The Orchestrator coordinates this workflow. It does not own department
responsibilities, engineering state, policy decisions, validation results, or
artifact persistence.

## Core Subsystems

- **Architect:** converts user intent into structured engineering direction.
- **Work Orders:** own task state, lifecycle, contract, acceptance criteria,
  deliverables, and persistent identity.
- **Repository Intelligence:** owns repository scanning, profiling, dependency
  graph metadata, module registry, alias registry, and repository indexes.
- **File Selection:** owns engineering reasoning about which files matter,
  selection evidence, confidence breakdowns, and escalation when evidence is
  insufficient.
- **Context Builder:** owns `EngineeringContext` packaging from Work Orders,
  repository profiles, and file-selection results.
- **Developer:** owns implementation generation.
- **Reviewer:** owns engineering and security review before verification.
- **Verify:** owns executable verification after Reviewer approval.
- **Historian:** owns persistent engineering memory and audit history.
- **Policy Engine:** owns governance decisions.
- **Safe Artifact Writer:** owns approved artifact mutation and filesystem
  safety enforcement.
- **Validation Harness:** owns independent release validation.
- **Engineering Transaction Protocol:** owns deterministic ownership transfer
  between departments.

## Read Before Editing

Read these files before making any modification:

- [ARCHITECTURE.md](ARCHITECTURE.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/ENGINEERING_GUIDE.md](docs/ENGINEERING_GUIDE.md)
- [docs/DECISIONS.md](docs/DECISIONS.md)
- [docs/ROADMAP.md](docs/ROADMAP.md)
- [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- [docs/validation.md](docs/validation.md)
- [RELEASE_SUMMARY.md](RELEASE_SUMMARY.md)

If you are working on handoffs or ownership transfer, also read:

- [handoffs/CONTRACT.md](handoffs/CONTRACT.md)
- [docs/ADR/0001-persistent-work-order-identity.md](docs/ADR/0001-persistent-work-order-identity.md)
- [docs/ADR/0002-work-order-workspace-ownership.md](docs/ADR/0002-work-order-workspace-ownership.md)

## Branch To Work On

- `main` is release-ready only.
- `development` is the normal integration branch for milestone work.
- Feature and fix branches should branch from `development`.
- Tagged releases are immutable release points. Current stable release is
  `v0.4.3`.

Use another branch only when the milestone or repository maintainer explicitly
requires it.

## Quick Start

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

Mock pipeline execution:

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

Validation reports are written to:

```text
reports/latest.json
reports/latest.md
reports/history/
```

## Validation Status

v0.4.3 is documented as GREEN after the release validation campaign covering:

- filesystem safety
- reviewer regression and adversarial cases
- architect normalization and retry fallback
- historian persistence
- UTF-8 artifact handling
- verify gating
- project context logging
- Work Orders
- Engineering Transaction Protocol integration
- Repository Intelligence
- File Selection
- Context Builder

Do not weaken validation to make a release pass. Fix the defect or document the
blocker.

## Repository Layout To Know

```text
repository_intelligence/   scanning, profiling, dependency graph, indexes
file_selection/            file-selection reasoning and evidence
context_builder/           EngineeringContext packaging
work_orders/               Work Order domain model and persistent identity
etp/                       Engineering Transaction Protocol
validation/                release validation harness and suites
reporters/                 JSON, Markdown, and release-summary reporters
reports/                   generated validation reports
output/
  work_orders/
    WO-000001/             canonical Work Order workspace layout
docs/                      onboarding, roadmap, decisions, validation docs
```

## Architecture Preservation Rule

Architectural intent must be preserved unless a milestone explicitly requires a
change. Do not silently move ownership between subsystems. If a milestone
requires architecture to change, record the decision in an ADR and update the
canonical architecture documentation.
