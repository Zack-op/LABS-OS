# Architectural Decisions

This file records architectural decisions already reflected in the codebase.
Detailed ADR files for v0.4.3 ownership decisions live in
[ADR/](ADR/).

Status values:

- Accepted
- Superseded
- Deferred

## ADR-0001: Policies Reference Capabilities, Not Model IDs

Status: Accepted

Decision:

`policies.yaml` references capability names. `capabilities.yaml` maps
capabilities to providers and models.

Consequences:

- model/provider swaps do not require policy changes
- policy validation can enforce no executable model IDs
- capability routing remains separate from governance

Related files:

- `policies.yaml`
- `capabilities.yaml`
- `capability_router.py`
- `llm_router.py`

## ADR-0002: Evidence-Driven Decisions, No LLM Self-Confidence

Status: Accepted

Decision:

Confidence is derived from measurable evidence such as validation results,
review findings, retries, policy events, and historical outcomes. LLM
self-reported confidence is not a release gate.

Related files:

- `historian.py`
- `validation/`
- `reports/`

## ADR-0003: Historian Records, Humans Govern

Status: Accepted

Decision:

Historian records events, failures, review evidence, and policy signals. It may
surface patterns, but it does not edit policies or make workflow decisions.

Related files:

- `historian.py`
- `policy_engine.py`
- `policies.yaml`

## ADR-0004: Reviewer Runs Before Verify

Status: Accepted

Decision:

Reviewer is a required gate before Verify. Reviewer failure stops the pipeline
and prevents verification execution.

Related files:

- `orchestrator.py`
- `validation/suites/reviewer_regression.py`
- `validation/suites/reviewer_adversarial.py`
- `validation/suites/verify_gating.py`

## ADR-0005: Architect Output Is Strictly Validated With Retry and Fallback

Status: Accepted

Decision:

Architect output is parsed strictly. The system retries once on malformed
output. If still invalid, it uses a deterministic documented fallback and logs
raw output plus validation errors.

Related files:

- `orchestrator.py`
- `validation/suites/architect_normalization.py`
- `validation/suites/retry_fallback.py`

## ADR-0006: Release Validation Harness Is Separate From Runtime

Status: Accepted

Decision:

The release harness lives in `validation/` and reports through `reporters/`.
It validates the organization from outside the runtime pipeline.

Related files:

- `validation/`
- `reporters/`
- `reports/`

## ADR-0007: Unsafe Artifact Paths Are Rejected, Not Normalized

Status: Accepted

Decision:

`SafeArtifactWriter` rejects unsafe artifact operations. It does not silently
normalize traversal, absolute paths, invalid names, protected-file writes, or
duplicate collisions.

Related files:

- `safe_artifact_writer.py`
- `policies.yaml`
- `historian.py`
- `validation/suites/filesystem_safety.py`

## ADR-0008: Duplicate Artifacts Are Deterministically Rejected

Status: Accepted

Decision:

Duplicate artifact collisions are rejected instead of overwritten or repaired
with timestamps.

Related files:

- `safe_artifact_writer.py`
- `validation/suites/filesystem_safety.py`

## ADR-0009: Work Orders Are Canonical Engineering State

Status: Accepted

Decision:

Work Orders own engineering task state, lifecycle, contract, acceptance
criteria, deliverables, and persistent identity. Natural-language prompts must
not become the durable department contract.

Related files:

- `work_orders/`
- `validation/suites/work_orders.py`

## ADR-0010: Work Order IDs Are Sequential and Deterministic

Status: Accepted

Decision:

Work Order IDs use `WO-000001` style sequential identifiers. UUIDs, timestamps,
and random IDs are not used for durable Work Order identity.

Related files:

- `work_orders/ids.py`
- `work_orders/state.py`
- `work_orders/state/work_order_counter.json`
- `validation/suites/work_orders.py`

## ADR-0011: Work Order Contracts Include Inputs, Outputs, Preconditions, and Postconditions

Status: Accepted

Decision:

The Work Order schema includes a `contract` section with `inputs`, `outputs`,
`preconditions`, and `postconditions`.

Related files:

- `work_orders/models.py`
- `work_orders/schema.py`
- `validation/suites/work_orders.py`

## ADR-0012: Separate Work Order State From Department Transfer Behavior

Status: Accepted

Decision:

Work Orders own engineering state. Engineering Transaction Protocol owns
ownership transfer between departments. Historian owns audit history.
Validation owns correctness gates. Policy Engine owns governance.

Consequences:

- Work Order schema remains focused on task state.
- ETP records transfer behavior only.
- Historian stores transfer evidence but does not decide validity.
- Validation proves behavior but does not own runtime state.
- Future departments can integrate without redefining ownership boundaries.

Related files:

- `work_orders/`
- `etp/`
- `handoffs/CONTRACT.md`
- `validation/suites/etp_integration.py`

## ADR-0013: Repository Intelligence Owns Static Repository Knowledge

Status: Accepted

Decision:

Repository Intelligence owns scanning, profiling, dependency graph, module
registry, alias registry, repository type, and metadata indexes.

It does not own file-selection decisions or context packaging.

Related files:

- `repository_intelligence/`
- `validation/suites/repo_intelligence.py`

## ADR-0014: File Selection Owns Relevant-File Reasoning

Status: Accepted

Decision:

File Selection owns rule traces, evidence, confidence breakdown, selected
files, exclusions, and escalation when evidence is insufficient.

Related files:

- `file_selection/`
- `validation/suites/file_selection.py`

## ADR-0015: Context Builder Owns EngineeringContext Packaging

Status: Accepted

Decision:

Context Builder packages Work Order data, repository profiles, and resolved
file selections into `EngineeringContext`. It refuses unresolved selections.

Related files:

- `context_builder/`
- `validation/suites/context_builder.py`

## ADR-0016: Work Order Workspace Ownership Is Canonical

Status: Accepted

Decision:

Work Order artifacts are organized under deterministic Work Order workspaces:

```text
output/
  work_orders/
    WO-000001/
```

Artifact mutation still flows through Safe Artifact Writer.

Detailed ADR:

- [ADR/0002-work-order-workspace-ownership.md](ADR/0002-work-order-workspace-ownership.md)
