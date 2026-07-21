# Engineering Transaction Protocol

The Engineering Transaction Protocol (ETP) is the planned Department Handoff
Infrastructure for AK Labs OS.

This directory defines the protocol contract only. It does not contain runtime
code, validation code, persistence code, or implementation details.

Read [CONTRACT.md](CONTRACT.md) for the canonical protocol contract.

## Purpose

ETP exists to make department handoffs explicit, deterministic, auditable, and
replayable.

In AK Labs OS, a department should not informally pass work to another
department through loose prompts or implicit state. A handoff should be a
structured transaction around one Work Order.

## Goals

- define one canonical mechanism for ownership transfer
- preserve Work Orders as the canonical engineering state
- preserve Historian as the canonical audit system
- preserve Validation Harness as the canonical validation authority
- preserve Policy Engine as the canonical governance authority
- support deterministic replay of department handoffs
- support future departments without redesigning ownership boundaries

## Relationship To Work Orders

Work Orders own engineering state.

ETP does not replace Work Orders and does not own Work Order schema, acceptance
criteria, deliverables, constraints, status history, or contract fields.

ETP owns the transfer of responsibility for a Work Order from one department or
owner to another.

## Relationship To Historian

Historian owns audit history.

ETP should produce transaction records that Historian can persist when runtime
implementation begins. Historian records the transfer history; it does not
decide whether a transfer is valid.

## Relationship To Validation

The Validation Harness owns correctness checks.

Future ETP validation should prove transfer determinism, single active owner
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

## Planned Implementation Phases

1. Contract: define the implementation-independent protocol contract.
2. Specification: define transaction envelope, validation cases, and storage
   expectations without changing runtime behavior.
3. Domain implementation: add ETP data structures and validation in isolation.
4. Runtime integration: make department handoffs use ETP once Work Order
   integration is explicitly in scope.
5. Historian integration: persist accepted and rejected transactions as audit
   history.

Each phase must preserve ADR-0012: Work Orders own engineering state, ETP owns
ownership transfer, and Historian owns audit history.

## Directory Overview

```text
handoffs/
  README.md    Overview and contributor entry point
  CONTRACT.md  Canonical Engineering Transaction Protocol contract
```

No executable files belong in this directory during the contract sprint.
