# START HERE

This file is for future AK Labs OS contributors, including AI coding agents.
Read it before changing the repository.

## What AK Labs OS Is

AK Labs OS is an early persistent AI Engineering Organization, not a generic
coding assistant. Its purpose is to coordinate engineering work through
departments, policy gates, validation, memory, safe artifact handling, and
structured Work Orders.

The Work Order is the canonical engineering object. The planned Engineering
Transaction Protocol (ETP) is the canonical ownership-transfer mechanism for
v0.4.2 work; it is not implemented yet.

Current release readiness is documented in [RELEASE_SUMMARY.md](RELEASE_SUMMARY.md).

## Where Architecture Is Documented

Read these first:

1. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - current system architecture.
2. [docs/ENGINEERING_GUIDE.md](docs/ENGINEERING_GUIDE.md) - how to work in the repo.
3. [docs/DECISIONS.md](docs/DECISIONS.md) - architectural decisions already made.
4. [docs/ROADMAP.md](docs/ROADMAP.md) - implemented milestones and planned work.
5. [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) - branch, validation, and release workflow.

The root [ARCHITECTURE.md](ARCHITECTURE.md) is the original architecture
constitution. The `docs/` directory is the canonical onboarding layer.

## Which Branch To Work On

Use the intended branch model:

- `main`: release-ready code only.
- `development`: integration branch for completed milestone work.
- milestone or task branches: short-lived branches from `development`.
- tagged releases: immutable release points such as `v0.4.1-alpha`.

If the local checkout does not expose Git metadata, still follow this workflow
conceptually and keep changes scoped to the requested milestone.

## How To Validate Changes

Use the Release Validation Harness:

```bash
python -m validation.cli release --deterministic
python -m validation.cli regression --deterministic
python -m validation.cli adversarial --deterministic
python -m validation.cli dod --deterministic
```

Reports are written to `reports/latest.json`, `reports/latest.md`, and
`reports/history/`.

For documentation-only changes, do not edit validation logic or runtime code
to make validation pass.

## Architecture Freeze Policy

Architecture is approved before implementation.

Implementation follows the approved architecture. It must not silently redefine
department responsibilities, Work Order ownership, policy authority, validation
authority, Historian audit boundaries, or filesystem safety rules.

Architectural changes require an ADR in [docs/DECISIONS.md](docs/DECISIONS.md).
Implementation-only milestones may not introduce new architecture unless the
milestone explicitly says so.

## Files To Read Before Modifying Behavior

Read these before changing runtime, validation, policy, or Work Order behavior:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DECISIONS.md](docs/DECISIONS.md)
- [RELEASE_SUMMARY.md](RELEASE_SUMMARY.md)
- [policies.yaml](policies.yaml)
- [capabilities.yaml](capabilities.yaml)
- [orchestrator.py](orchestrator.py)
- [policy_engine.py](policy_engine.py)
- [historian.py](historian.py)
- [safe_artifact_writer.py](safe_artifact_writer.py)
- [work_orders/schema.py](work_orders/schema.py)
- [validation/registry.py](validation/registry.py)

## Preservation Rule

Architectural intent must be preserved unless the active milestone explicitly
requires a change.

Do not redesign departments, policies, validation, filesystem safety, Work
Orders, or runtime flow as a side effect of another task. If a change would
alter architectural intent, document the reason in [docs/DECISIONS.md](docs/DECISIONS.md).
