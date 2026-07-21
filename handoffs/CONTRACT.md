# Engineering Transaction Protocol Contract

This document defines the canonical Engineering Transaction Protocol (ETP) for
AK Labs OS.

The contract is implementation-independent. It defines what a valid department
handoff must mean, not how a runtime implementation stores or executes it.

## Purpose

ETP is the canonical ownership-transfer mechanism between AK Labs OS
departments.

Its purpose is to make every department handoff explicit, deterministic,
auditable, and replayable while preserving the Work Order as the canonical
engineering object.

## Scope

ETP covers ownership transfer for one Work Order from one department or owner
to another.

In scope:

- transfer intent
- source ownership
- destination ownership
- required transfer metadata
- required evidence
- accepted or rejected transaction outcome
- replayable transaction history

Out of scope:

- Work Order schema ownership
- validation result ownership
- policy rule ownership
- artifact persistence
- repository intelligence
- context construction
- runtime implementation details

## Responsibilities

ETP is responsible for:

- defining a canonical handoff transaction
- ensuring every transaction references exactly one Work Order
- ensuring every transaction has exactly one source owner and one destination
  owner
- making ownership transfer explicit
- preserving deterministic transaction order
- defining evidence required for handoff
- producing an accepted or rejected transaction result
- supporting replay of ownership history from transaction records

## Non-Responsibilities

ETP is not responsible for:

- defining or mutating Work Order content
- deciding engineering correctness
- enforcing policies
- storing historical records as the canonical audit system
- writing or modifying artifacts
- selecting repository files
- constructing context packets
- executing department work
- creating approval queues

## Ownership Model

There is no responsibility overlap.

| Concern | Canonical owner |
|---|---|
| Engineering state | Work Orders |
| Ownership transfer | Engineering Transaction Protocol |
| Audit history | Historian |
| Correctness and release validation | Validation Harness |
| Governance and escalation | Policy Engine |
| Artifact persistence | Safe Artifact Writer |
| Repository knowledge | Repository Intelligence, planned |
| Context construction | Context Builder, planned |

Rules:

- Work Orders own engineering state.
- ETP owns ownership transfer.
- Historian owns audit history.
- Validation owns correctness.
- Policy Engine owns governance.
- Safe Artifact Writer owns artifact persistence.

ETP may reference records from other owners. It must not become their source of
truth.

## Transaction Lifecycle

A transaction conceptually follows this flow:

```text
Draft Transfer Intent
    |
    v
Validate Source Ownership
    |
    v
Validate Destination
    |
    v
Attach Evidence
    |
    v
Evaluate Required Policy Gates
    |
    v
Accept or Reject Transfer
    |
    v
Emit Historian Audit Record
```

This lifecycle is conceptual. It does not define classes, functions, database
tables, queues, or runtime control flow.

Rejected transactions remain part of history. A rejected transaction does not
change active ownership.

Accepted transactions transfer active ownership to the destination owner.

## Inputs

Every transaction requires:

- protocol version
- deterministic transaction ID
- deterministic sequence number
- Work Order ID
- source department
- source owner
- destination department
- destination owner
- initiating actor or department
- transfer reason
- transfer intent
- current Work Order reference or snapshot reference
- evidence package
- policy decision references when policy gates are required
- validation references when validation has already occurred
- previous transaction reference when one exists

The transaction must not depend on hidden conversation state.

## Outputs

Every transaction produces one of two outcomes:

- accepted transfer record
- rejected transfer record

Every output record includes:

- transaction metadata
- outcome
- reason for acceptance or rejection
- active owner after evaluation
- evidence references accepted with the transaction
- policy references used by the transaction
- validation references used by the transaction
- Historian audit payload or reference

ETP does not directly produce generated code, modified files, reports, policy
changes, or Work Order schema changes.

## Required Metadata

Every transaction record must include:

- `protocol_version`
- `transaction_id`
- `sequence_number`
- `work_order_id`
- `source_department`
- `source_owner`
- `destination_department`
- `destination_owner`
- `initiated_by`
- `transfer_reason`
- `transfer_intent`
- `previous_transaction_id`
- `outcome`
- `outcome_reason`
- `active_owner_after`
- `evidence_refs`
- `policy_refs`
- `validation_refs`
- `created_at`

Metadata rules:

- transaction IDs must be deterministic
- sequence numbers, not timestamps, define replay order
- `created_at` is audit metadata, not an ordering authority
- `previous_transaction_id` is `null` only for the first transaction for a Work
  Order
- `active_owner_after` remains the source owner when a transaction is rejected

## Evidence Requirements

Every transaction must carry enough evidence for another process to understand
why ownership changed or why transfer was rejected.

Minimum evidence:

- Work Order reference
- source department completion statement or handoff reason
- destination department readiness basis
- required deliverable references, if any
- required review references, if any
- required validation references, if any
- required policy decision references, if any

Evidence rules:

- accepted evidence is immutable
- evidence must be referenced explicitly
- evidence must not rely on hidden chat context
- evidence may reference artifacts, but artifact persistence remains owned by
  Safe Artifact Writer
- evidence may reference validation results, but validation authority remains
  with the Validation Harness

## Validation Expectations

Future validation must prove:

- one Work Order per transaction
- exactly one active owner after every accepted transaction
- rejected transactions do not transfer ownership
- source owner must match current active owner
- destination department must be valid
- transaction sequence is deterministic
- transaction replay reconstructs ownership history
- missing required metadata is rejected
- missing required evidence is rejected
- policy-gated transfers require policy references
- accepted evidence remains immutable

The Validation Harness owns these checks. ETP does not own validation results.

## Retry Philosophy

Retries must preserve auditability.

Rules:

- a failed or rejected transaction is never overwritten
- a retry references the transaction it follows
- identical retry attempts should be idempotent when the future implementation
  supports idempotency
- changed evidence creates a new transaction attempt
- retries must not create multiple active owners
- retries must not mutate accepted evidence from prior attempts

Retries are part of history, not hidden control flow.

## Extension Points

ETP may be extended by adding:

- new department names
- new transfer intents
- new evidence reference types
- new policy reference types
- new validation reference types
- new Historian storage backends

Extensions must not:

- move Work Order state ownership into ETP
- move audit ownership out of Historian
- move validation ownership out of the Validation Harness
- move policy ownership out of Policy Engine
- move artifact persistence out of Safe Artifact Writer
- require redesign of existing transaction records

## Protocol Invariants

The protocol must always preserve these invariants:

- exactly one active owner
- immutable transaction history
- deterministic ownership transfer
- one Work Order per transaction
- replayable transactions
- append-only history
- accepted evidence is immutable
- explicit ownership at every stage
- rejected transactions do not change ownership
- timestamps never determine ownership order
- no hidden department handoffs
- no duplicate canonical owner for any engineering concern
