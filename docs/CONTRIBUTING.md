# Contributing

Read [START_HERE.md](../START_HERE.md) first. This project is intended for
human engineers and AI coding agents working against explicit milestones.

## Contribution Standard

Every change must preserve architectural intent unless the milestone explicitly
requires a change.

Do not make incidental changes to:

- runtime pipeline behavior
- policies
- validation gates
- filesystem safety
- Work Order schema or lifecycle
- Historian behavior
- model routing

If a milestone requires architectural change, document the decision in
[DECISIONS.md](DECISIONS.md).

## Architecture Freeze Policy

Architecture is approved before implementation. Implementation must follow the
approved architecture and must not silently redefine it.

Architecture changes require:

- an explicit milestone requirement
- an ADR in [DECISIONS.md](DECISIONS.md)
- updates to [ARCHITECTURE.md](ARCHITECTURE.md) and [ROADMAP.md](ROADMAP.md)
- validation planning when implementation will follow

## Branching Strategy

Intended branch model:

- `main`: release-ready code only
- `development`: integration branch for completed milestone work
- `feature/<short-name>`: implementation branches from `development`
- `fix/<short-name>`: targeted defect branches from `development`
- tags: immutable release points such as `v0.4.1-alpha`

Release candidates should merge into `development`, pass the full Release
Validation Harness, then merge to `main` and receive a version tag.

If the local environment does not expose Git metadata, still structure work as
if this model is active.

## Validation Workflow

Before changing code:

1. Read the relevant docs and ADRs.
2. Identify which validation suite should catch regressions.
3. Confirm whether runtime behavior is allowed to change.

After changing code:

```bash
python -m validation.cli release --deterministic
python -m validation.cli regression --deterministic
python -m validation.cli adversarial --deterministic
python -m validation.cli dod --deterministic
```

For documentation-only changes, do not modify validation logic. A documentation
change may be delivered without rerunning all runtime suites if no executable
files changed, but the final handoff must say that runtime validation was not
rerun.

## Release Lifecycle

1. Milestone objective is defined.
2. Implementation is scoped to the milestone.
3. Focused validation is run.
4. Full release validation is run.
5. `reports/latest.*` and `reports/history/*` are generated.
6. `RELEASE_SUMMARY.md` is updated with evidence.
7. Suggested version is recorded.
8. Release is tagged after the code is on `main`.

Release readiness is based on evidence, not optimism.

## Documentation Expectations

Update docs when a change affects:

- architecture
- release process
- validation workflow
- subsystem responsibilities
- roadmap
- architectural decisions

Use these files:

- [ARCHITECTURE.md](ARCHITECTURE.md) for system structure
- [ENGINEERING_GUIDE.md](ENGINEERING_GUIDE.md) for working practices
- [ROADMAP.md](ROADMAP.md) for milestone planning
- [DECISIONS.md](DECISIONS.md) for ADRs
- [../RELEASE_SUMMARY.md](../RELEASE_SUMMARY.md) for release evidence

## Validation and Reports

The validation harness must remain separate from the runtime pipeline.

Do not:

- make runtime code depend on validation harness internals
- weaken validation to pass a release
- hide failed gates
- silently ignore malformed outputs

Do:

- add regression checks for historical defects
- record evidence in machine-readable JSON
- keep human-readable Markdown reports
- preserve deterministic mode

## Security and Filesystem Rules

Runtime artifact writes should go through `SafeArtifactWriter`.

Unsafe writes must be blocked and recorded through policy and Historian.
Never silently normalize unsafe paths.

## Work Order Rules

Work Orders are the planned department contract. In v0.4.1 they are available
but not mandatory at runtime.

Do not change the schema, lifecycle, or validation rules casually. Schema
changes need:

- a milestone requirement
- validation updates
- documentation updates
- an ADR

## Engineering Transaction Protocol Rules

ETP is planned as v0.4.2 Department Handoff Infrastructure. It is the planned
canonical ownership-transfer mechanism, not a replacement for Work Orders,
Historian, Policy Engine, Validation Harness, or Safe Artifact Writer.

Do not implement ETP during documentation-only reconciliation work. Do not move
responsibilities into ETP that already have canonical owners.

## Review Checklist

Before handing off:

- Is the change limited to the requested milestone?
- Were unrelated refactors avoided?
- Did runtime behavior change only when allowed?
- Were validation gates preserved?
- Are implemented and planned features clearly separated in docs?
- Is any new architectural decision documented?
