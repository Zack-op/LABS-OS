# Architectural Decisions

This file records decisions already reflected in the codebase. Use concise ADRs
for new architecture decisions.

Status values:

- Accepted
- Superseded
- Deferred

## ADR-0001: Policies Reference Capabilities, Not Model IDs

Status: Accepted

Context:

Models and providers change frequently. Policy rules should not churn every
time a model is replaced.

Decision:

`policies.yaml` references capability names. `capabilities.yaml` maps those
capabilities to concrete providers and models.

Consequences:

- model/provider swaps do not require policy changes
- policy validation can enforce no executable model IDs
- capability resolution becomes its own subsystem

Related files:

- `policies.yaml`
- `capabilities.yaml`
- `capability_router.py`
- `llm_router.py`

## ADR-0002: Evidence-Driven Decisions, No LLM Self-Confidence

Status: Accepted

Context:

The system is intended to reduce fabricated certainty. Model-reported
confidence would create another unverified claim.

Decision:

Confidence scores are not accepted from LLM self-reporting. Decisions use
measurable evidence such as validation results, retries, review findings,
policy logs, and historical outcomes.

Consequences:

- no self-confidence field is used as a release gate
- Historian can later compute evidence-based confidence
- validation remains the source of truth

Related files:

- `historian.py`
- `validation/`
- `RELEASE_SUMMARY.md`

## ADR-0003: Historian Suggests, Humans Decide

Status: Accepted

Context:

Organizational memory should surface patterns without silently rewriting
governance.

Decision:

Historian records policy evidence and repeated escalation candidates. It does
not edit `policies.yaml` automatically.

Consequences:

- repeated escalation candidates stay pending until human decision
- policy edits remain explicit
- memory and governance are separated

Related files:

- `historian.py`
- `policy_engine.py`
- `policies.yaml`

## ADR-0004: Reviewer Runs Before Verify

Status: Accepted

Context:

Syntax-valid insecure code must not proceed to validation as if it were
acceptable.

Decision:

The pipeline order is Architect -> Developer -> Reviewer -> Verify -> Commit
message.

Consequences:

- Reviewer failure stops the pipeline
- Verify does not execute after Reviewer failure
- review artifacts are recorded before later gates

Related files:

- `orchestrator.py`
- `validation/suites/verify_gating.py`
- `validation/suites/reviewer_regression.py`

## ADR-0005: Architect Output Is Strictly Validated With Retry and Fallback

Status: Accepted

Context:

Live provider responses can include malformed JSON, markdown fences, or
reasoning text.

Decision:

Architect output is parsed strictly. The system retries once on invalid output.
If still invalid, it uses a deterministic documented fallback and logs raw
output plus validation errors.

Consequences:

- malformed responses are not silently ignored
- fallback is explicit and auditable
- downstream stages receive a valid structured brief

Related files:

- `orchestrator.py`
- `validation/suites/architect_normalization.py`
- `validation/suites/retry_fallback.py`

## ADR-0006: Release Validation Harness Is Separate From Runtime

Status: Accepted

Context:

The organization needs independent validation infrastructure that can judge the
runtime without becoming part of it.

Decision:

The release harness lives in `validation/` and reports through `reporters/`.
It uses isolated temporary workspaces and writes only reports plus release
summary updates to the repository.

Consequences:

- runtime code does not depend on validation internals
- release gates are deterministic
- JSON and Markdown evidence is preserved

Related files:

- `validation/`
- `reporters/`
- `reports/`

## ADR-0007: Unsafe Artifact Paths Are Rejected, Not Normalized

Status: Accepted

Context:

Silent path repair hides security problems and can overwrite unexpected files.

Decision:

`SafeArtifactWriter` rejects unsafe artifact operations. It does not silently
normalize traversal, absolute paths, invalid names, protected-file writes, or
duplicate collisions.

Consequences:

- blocked writes return structured failures
- blocked writes produce policy events
- Historian persists blocked filesystem events

Related files:

- `safe_artifact_writer.py`
- `policies.yaml`
- `historian.py`
- `validation/suites/filesystem_safety.py`

## ADR-0008: Duplicate Artifacts Are Deterministically Rejected

Status: Accepted

Context:

Timestamp-based unique names would weaken deterministic validation and artifact
provenance.

Decision:

Duplicate artifact collisions are rejected instead of overwritten or repaired
with timestamps.

Consequences:

- reruns expose collision problems
- artifact provenance remains clear
- deterministic validation is preserved

Related files:

- `safe_artifact_writer.py`
- `validation/suites/filesystem_safety.py`

## ADR-0009: Work Orders Are Available Before They Are Mandatory

Status: Accepted

Context:

The organization needs a canonical engineering contract, but immediate runtime
integration would mix domain-model design with pipeline behavior changes.

Decision:

v0.4.1 implements the Work Order Domain Model as a standalone package. Runtime
departments may continue using the current internal brief/prompt flow until a
future milestone makes Work Orders mandatory.

Consequences:

- schema and lifecycle can stabilize independently
- release validation protects the domain model
- v0.4.2 can focus on integration

Related files:

- `work_orders/`
- `validation/suites/work_orders.py`

## ADR-0010: Work Order IDs Are Sequential and Deterministic

Status: Accepted

Context:

Work Orders must be readable, reproducible, and easy for humans and agents to
reference.

Decision:

Work Order IDs use `WO-000001` style sequential IDs. UUIDs, timestamps, and
random IDs are not used.

Consequences:

- validation can prove deterministic ID behavior
- handoffs are easier to reference
- future persistence must coordinate sequence allocation

Related files:

- `work_orders/ids.py`
- `validation/suites/work_orders.py`

## ADR-0011: Work Order Contracts Include Inputs, Outputs, Preconditions, and Postconditions

Status: Accepted

Context:

Future implementers need executable engineering contracts, not passive tickets.

Decision:

The Work Order schema includes a `contract` section with `inputs`, `outputs`,
`preconditions`, and `postconditions`.

Consequences:

- future departments can reason about required context and expected artifacts
- validation can enforce structured contracts
- Work Orders can later support automated execution planning

Related files:

- `work_orders/models.py`
- `work_orders/schema.py`
- `validation/suites/work_orders.py`

## ADR-0012: Separate Work Order State from Department Transfer Behavior

Status: Accepted

Context:

v0.4.1 introduced the Work Order Domain Model as the canonical structured
engineering object. The next planned milestone introduces department handoff
infrastructure. Without a boundary, future implementation could overload Work
Orders with transfer behavior, overload Historian with workflow authority, or
create competing state machines.

Problem Statement:

AK Labs OS needs explicit department handoffs, but ownership transfer is not
the same concern as engineering state. Work Orders describe the task and its
contract. A handoff protocol describes who owns the task next and why. If one
subsystem owns both concerns implicitly, future agents will have ambiguous
authority and weaker auditability.

Decision:

Keep Work Orders as the canonical engineering state. Introduce the planned
Engineering Transaction Protocol (ETP) as the canonical ownership-transfer
mechanism between departments. Historian remains the canonical audit system.
The Validation Harness remains the canonical validation authority. The Policy
Engine remains the canonical policy enforcement system.

Consequences:

- Work Order schema and lifecycle remain focused on engineering state.
- ETP owns department transfer behavior only.
- Historian records transfer evidence but does not decide transfer validity.
- Validation proves transfer behavior but does not own transfer state.
- Future repository intelligence and context construction can integrate without
  redefining Work Order ownership.

Migration Strategy:

- v0.4.2A documents and freezes the architecture only.
- v0.4.2B should specify the ETP transaction envelope and validation cases.
- A later implementation milestone may introduce ETP code without changing the
  Work Order schema unless explicitly required.
- Runtime departments may continue using current brief/prompt flow until an
  implementation milestone makes ETP and Work Orders mandatory.

Rejected Alternatives:

- Put transfer behavior inside Work Orders. Rejected because it mixes
  engineering state with ownership-transfer mechanics.
- Make Historian responsible for transfers. Rejected because Historian records
  history; it should not own workflow authority.
- Let each department hand off informally. Rejected because implicit transfer
  weakens auditability and deterministic validation.
- Build repository intelligence first. Rejected because repository knowledge
  depends on a stable task and handoff contract.

Non-Goals:

- implementing ETP during this documentation sprint
- changing runtime orchestrator behavior
- changing Work Order schema or lifecycle
- adding repository intelligence
- adding approval queue behavior
- redesigning Historian, Policy Engine, Validation Harness, or Safe Artifact
  Writer

Related Files:

- `docs/ARCHITECTURE.md`
- `docs/ROADMAP.md`
- `START_HERE.md`
- `work_orders/`
- `historian.py`
- `validation/`
