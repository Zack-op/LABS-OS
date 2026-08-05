# Engineering Guide

Start with [../START_HERE.md](../START_HERE.md). For the canonical ownership
model, read [../ARCHITECTURE.md](../ARCHITECTURE.md). For architectural
decisions, read [DECISIONS.md](DECISIONS.md).

## Engineering Principles

- Preserve architectural intent unless the active milestone explicitly requires
  a change.
- Keep each department single-purpose.
- Keep policies free of model IDs.
- Prefer deterministic behavior and replayable evidence.
- Reject unsafe filesystem paths instead of repairing them.
- Validate claims through the Release Validation Harness.
- Record architectural decisions as ADRs.
- Keep runtime execution separate from release validation infrastructure.

## Local Setup

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

Provider keys are operator configuration. Mock mode does not require live LLM
credentials.

## Running the Pipeline

Mock mode:

```powershell
python orchestrator.py "Build a function that validates an email address" --mock
```

Live mode:

```powershell
python orchestrator.py "Build a function that reverses a string"
```

## Validation Workflow

Run focused checks first when changing a subsystem. Run aggregate gates before
release handoff.

```powershell
python -m validation.cli release --deterministic
python -m validation.cli regression --deterministic
python -m validation.cli adversarial --deterministic
python -m validation.cli dod --deterministic
```

Reports:

- `reports/latest.json`
- `reports/latest.md`
- `reports/history/`

Do not weaken validation to pass a release. Fix the defect or record the
blocker.

## Repository Layout

Runtime and governance:

- `orchestrator.py` - workflow coordination only
- `policy_engine.py` - policy evaluation
- `historian.py` - persistent engineering memory
- `safe_artifact_writer.py` - artifact mutation and filesystem safety
- `capability_router.py` - capability to provider/model resolution
- `llm_router.py` - model call routing and mock execution

Engineering organization packages:

- `work_orders/` - Work Order schema, IDs, lifecycle, contracts, persistence
- `repository_intelligence/` - scanning, profiles, dependency graph, indexes
- `file_selection/` - file reasoning, traces, confidence, escalation
- `context_builder/` - `EngineeringContext` packaging
- `etp/` - ownership transfer records and validation

Release infrastructure:

- `validation/` - validation harness and suites
- `reporters/` - JSON and Markdown report writers
- `reports/` - generated validation evidence

Documentation:

- `START_HERE.md`
- `ARCHITECTURE.md`
- `docs/`
- `CHANGELOG.md`
- `PROJECT_STATUS.md`
- `RELEASE_NOTES_v0.4.3.md`

Generated Work Order artifacts:

```text
output/
  work_orders/
    WO-000001/
```

## Files To Read Before Specific Changes

Runtime pipeline:

- `ARCHITECTURE.md`
- `docs/ARCHITECTURE.md`
- `orchestrator.py`
- `policies.yaml`
- `policy_engine.py`

Repository intelligence:

- `repository_intelligence/scanner.py`
- `repository_intelligence/intelligence.py`
- `repository_intelligence/models.py`
- `validation/suites/repo_intelligence.py`

File selection:

- `file_selection/engine.py`
- `file_selection/rules.py`
- `file_selection/models.py`
- `validation/suites/file_selection.py`

Context building:

- `context_builder/builder.py`
- `context_builder/models.py`
- `validation/suites/context_builder.py`

Work Orders and ownership:

- `work_orders/`
- `etp/`
- `handoffs/CONTRACT.md`
- `docs/ADR/`

Filesystem safety:

- `safe_artifact_writer.py`
- `policies.yaml`
- `validation/suites/filesystem_safety.py`

Release validation:

- `validation/registry.py`
- `validation/runner.py`
- `validation/dod.py`
- `validation/suites/`
- `docs/validation.md`

## Safe Artifact Rules

Runtime artifact mutation should go through `SafeArtifactWriter`.

Unsafe operations must be blocked and recorded:

- traversal
- absolute paths
- writes outside approved workspace
- invalid or reserved filenames
- duplicate artifact collisions
- protected project-file writes without explicit authorization
- symlink escapes where supported

The writer rejects unsafe paths. It does not silently normalize them.

## Work Order Rules

Work Orders are the canonical task-state objects. They carry deterministic
identity, lifecycle, acceptance criteria, deliverables, constraints, ownership
metadata, and contract fields.

Do not change the schema, lifecycle, identity model, or workspace ownership
without a milestone requirement and ADR.

## ETP Rules

Engineering Transaction Protocol owns ownership transfer between departments.
It does not own Work Order state, Historian persistence, validation
correctness, policy decisions, or artifact persistence.

Transfer evidence must be explicit and replayable.

## Documentation Rules

- Describe implemented behavior as implemented.
- Describe planned behavior only in the roadmap.
- Keep subsystem terminology consistent with [../ARCHITECTURE.md](../ARCHITECTURE.md).
- Update ADRs when architecture changes.
- Update release notes and changelog for release-level changes.
