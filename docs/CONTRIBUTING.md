# Contributing

Read [../START_HERE.md](../START_HERE.md) first. AK Labs OS is maintained as a
milestone-driven engineering organization, not as an open-ended coding prompt.

## Contribution Standard

Every change must preserve architectural intent unless the active milestone
explicitly requires a change.

Do not make incidental changes to:

- runtime pipeline behavior
- policies
- validation gates
- filesystem safety
- Work Order schema, identity, lifecycle, or workspace ownership
- Engineering Transaction Protocol ownership rules
- Historian behavior
- Repository Intelligence ownership
- File Selection ownership
- Context Builder ownership

If a milestone requires architectural change, record the decision in
[DECISIONS.md](DECISIONS.md) and update the architecture docs.

## Branching Strategy

Intended branch model:

- `main`: release-ready code only
- `development`: integration branch for completed milestone work
- `feature/<short-name>`: implementation branches from `development`
- `fix/<short-name>`: targeted defect branches from `development`
- tags: immutable release points such as `v0.4.3`

Release candidates should merge into `development`, pass the full Release
Validation Harness, then merge to `main` and receive a version tag.

## Validation Workflow

Before changing code:

1. Read the relevant docs and ADRs.
2. Identify the subsystem owner.
3. Confirm whether runtime behavior is allowed to change.
4. Identify which validation suite should catch regressions.

After changing code:

```powershell
python -m validation.cli release --deterministic
python -m validation.cli regression --deterministic
python -m validation.cli adversarial --deterministic
python -m validation.cli dod --deterministic
```

For documentation-only changes, do not modify validation logic. A documentation
change may be delivered without rerunning all runtime suites if no executable
files changed, but the handoff must say that runtime validation was not rerun.

## Release Lifecycle

1. Milestone objective is defined.
2. Implementation is scoped to the milestone.
3. Focused validation is run.
4. Full release validation is run.
5. `reports/latest.*` and `reports/history/*` are generated.
6. Release evidence is recorded.
7. Suggested version is recorded.
8. Release is tagged after the code is on `main`.

Release readiness is based on evidence.

## Documentation Expectations

Update docs when a change affects:

- architecture
- release process
- validation workflow
- subsystem responsibilities
- roadmap
- architectural decisions
- project status

Use these files:

- [../ARCHITECTURE.md](../ARCHITECTURE.md) for canonical subsystem ownership
- [ARCHITECTURE.md](ARCHITECTURE.md) for operational architecture guidance
- [ENGINEERING_GUIDE.md](ENGINEERING_GUIDE.md) for working practices
- [ROADMAP.md](ROADMAP.md) for milestone planning
- [DECISIONS.md](DECISIONS.md) for ADRs and decision index
- [validation.md](validation.md) for validation workflow and gates

## Security and Filesystem Rules

Runtime artifact writes should go through `SafeArtifactWriter`.

Unsafe writes must be blocked and recorded through policy and Historian. Never
silently normalize unsafe paths.

## Ownership Rules

- Work Orders own engineering state.
- ETP owns ownership transfer.
- Historian owns audit history.
- Validation owns correctness gates.
- Policy Engine owns governance.
- Safe Artifact Writer owns artifact mutation safety.
- Orchestrator owns workflow orchestration only.

Do not move responsibilities between these owners without an accepted ADR.

## Review Checklist

Before handing off:

- Is the change limited to the requested milestone?
- Were unrelated refactors avoided?
- Did runtime behavior change only when allowed?
- Were validation gates preserved?
- Are implemented and planned features clearly separated?
- Is any new architectural decision documented?
