# Engineering Guide

Start with [START_HERE.md](../START_HERE.md). For architecture, read
[ARCHITECTURE.md](ARCHITECTURE.md). For durable decisions, read
[DECISIONS.md](DECISIONS.md).

## Engineering Principles

AK Labs OS is optimized for organizational reliability before coding power.

Default rules:

- preserve architectural intent unless the milestone explicitly requires a
  change
- keep departments single-purpose
- keep policies free of model IDs
- prefer deterministic behavior
- reject unsafe filesystem paths instead of repairing them
- validate every claim with the Release Validation Harness
- document architectural decisions in [DECISIONS.md](DECISIONS.md)
- preserve the canonical owner for each engineering concern

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env
```

`GROQ_API_KEY` is optional for mock mode. Live mode depends on operator-supplied
provider keys.

## Running the Pipeline

Mock mode:

```bash
python orchestrator.py "Build a function that validates an email address" --mock
```

Live mode:

```bash
python orchestrator.py "Build a function that reverses a string"
```

Mock mode is the normal path for validating pipeline mechanics without external
model calls.

## Validation Workflow

Run focused checks first when touching a subsystem. Then run aggregate gates.

```bash
python -m validation.cli release --deterministic
python -m validation.cli regression --deterministic
python -m validation.cli adversarial --deterministic
python -m validation.cli dod --deterministic
```

Reports:

- `reports/latest.json`
- `reports/latest.md`
- `reports/history/`

Expected behavior:

- `release` and `dod` must pass before a milestone is considered releasable
- `regression` protects known historical defects
- `adversarial` focuses on intentionally hostile Reviewer cases

Do not weaken a validation suite to make a change pass. Fix the defect or mark
the limitation honestly.

## Repository Layout

Runtime:

- `orchestrator.py` - current department pipeline
- `policy_engine.py` - policy loading, evaluation, and audit logging
- `historian.py` - organizational memory tables and queries
- `safe_artifact_writer.py` - approved artifact mutation layer
- `capability_router.py` - capability to provider/model resolution
- `llm_router.py` - model call routing and mock mode
- `dev_tools.py` - manual verification helpers

Configuration:

- `policies.yaml` - policy definitions
- `capabilities.yaml` - provider/model bindings
- `culture.yaml` - engineering culture seed
- `.env.example` - optional provider key template
- `requirements.txt` - pinned runtime dependencies

Domain model:

- `work_orders/` - Work Order schema, lifecycle, validation, serialization,
  and manager

Release infrastructure:

- `validation/` - validation harness and suites
- `reporters/` - JSON and Markdown report writers
- `reports/` - generated validation reports

Documentation:

- `START_HERE.md`
- `docs/`
- `RELEASE_SUMMARY.md`

## Files To Read Before Specific Changes

Runtime pipeline:

- `docs/ARCHITECTURE.md`
- `orchestrator.py`
- `policies.yaml`
- `policy_engine.py`
- `safe_artifact_writer.py`

Policy or capability routing:

- `docs/DECISIONS.md`
- `policies.yaml`
- `capabilities.yaml`
- `capability_router.py`
- `llm_router.py`

Historian:

- `historian.py`
- `policy_engine.py`
- `RELEASE_SUMMARY.md`

Filesystem safety:

- `safe_artifact_writer.py`
- `validation/suites/filesystem_safety.py`
- `policies.yaml`

Work Orders:

- `work_orders/schema.py`
- `work_orders/models.py`
- `work_orders/lifecycle.py`
- `work_orders/validator.py`
- `validation/suites/work_orders.py`

Release validation:

- `validation/registry.py`
- `validation/runner.py`
- `validation/dod.py`
- `validation/suites/`

## Adding or Changing Behavior

Before editing:

1. Identify the milestone objective.
2. Confirm whether runtime behavior is allowed to change.
3. Read the relevant decisions in [DECISIONS.md](DECISIONS.md).
4. Add or update validation only when the milestone requires it.
5. Keep edits scoped to the subsystem.

After editing:

1. Run focused validation.
2. Run aggregate validation.
3. Update `RELEASE_SUMMARY.md` only for release-relevant evidence.
4. Add an ADR if architectural intent changed.

## Safe Artifact Rules

Runtime project-artifact mutation should go through `SafeArtifactWriter`.

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

Work Orders are implemented but not yet mandatory at runtime.

Current status:

- available as a standalone domain model
- validated by the release harness
- JSON serialization implemented
- YAML reserved for future support

Do not force Work Orders into the orchestrator unless the active milestone
explicitly requires runtime integration.

## Engineering Transaction Protocol Rules

The Engineering Transaction Protocol is planned as v0.4.2 Department Handoff
Infrastructure.

Current status:

- planned architecture only
- not implemented
- not part of runtime behavior
- documented in [ARCHITECTURE.md](ARCHITECTURE.md) and
  [DECISIONS.md](DECISIONS.md)

ETP must own ownership-transfer behavior only. It must not become the owner of
Work Order schema, Historian records, validation results, policy decisions, or
artifact persistence.

## Architecture Freeze Rules

Architecture is approved before implementation. Implementation follows the
approved architecture.

Architectural changes require an ADR. Implementation must not silently redefine
architecture, department ownership, subsystem boundaries, or canonical sources
of truth.

## Documentation Rules

Keep documentation honest:

- separate implemented behavior from planned behavior
- do not describe aspirational features as shipped
- cross-reference canonical docs
- add ADRs for architecture decisions
- update roadmap after release milestones
