# Engineering Transaction Protocol

The Engineering Transaction Protocol (ETP) is the ownership-transfer protocol
for AK Labs OS departments.

This directory contains the protocol documentation. Runtime domain structures
live in `etp/`, and validation coverage lives in
`validation/suites/etp_integration.py`.

Read [CONTRACT.md](CONTRACT.md) for the canonical protocol contract.

## Purpose

ETP makes department handoffs explicit, deterministic, auditable, and
replayable.

In AK Labs OS, a department should not informally pass work to another
department through loose prompts or implicit state. A handoff is a structured
transaction around one Work Order.

## Goals

- define one canonical mechanism for ownership transfer
- preserve Work Orders as the canonical engineering state
- preserve Historian as the canonical audit system
- preserve Validation Harness as the canonical validation authority
- preserve Policy Engine as the canonical governance authority
- support deterministic replay of department handoffs
- support new departments without redesigning ownership boundaries

## Relationship To Work Orders

Work Orders own engineering state.

ETP does not replace Work Orders and does not own Work Order schema, acceptance
criteria, deliverables, constraints, status history, or contract fields.

ETP owns the transfer of responsibility for a Work Order from one department or
owner to another.

## Relationship To Historian

Historian owns audit history.

ETP produces transaction records that Historian can persist as audit evidence.
Historian records the transfer history; it does not decide whether a transfer is
valid.

## Relationship To Validation

The Validation Harness owns correctness checks.

ETP integration validation proves transfer determinism, single active owner
behavior, invalid transfer rejection, evidence completeness, and replayability.
ETP does not own validation results.

## Relationship To Policy Engine

Policy Engine owns governance.

ETP may require policy decisions before some transfers can proceed. The policy
decision remains owned by Policy Engine. ETP records or references the decision
as evidence for the transfer.

## Relationship To Safe Artifact Writer

Safe Artifact Writer owns artifact persistence.

ETP may reference artifacts produced by departments, but it does not write,
rename, delete, or persist project artifacts. Artifact mutation remains behind
Safe Artifact Writer.

## Implementation Status

- Protocol contract: complete
- Domain implementation: present in `etp/`
- Validation coverage: present in `validation/suites/etp_integration.py`
- Work Order relationship: established through Work Order IDs
- Historian relationship: ETP records are audit evidence; Historian remains the
  audit owner

Each implementation must preserve ADR-0012: Work Orders own engineering state,
ETP owns ownership transfer, and Historian owns audit history.

## Directory Overview

```text
handoffs/
  README.md    Overview and contributor entry point
  CONTRACT.md  Canonical Engineering Transaction Protocol contract
```
