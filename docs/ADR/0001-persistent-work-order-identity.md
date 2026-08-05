# ADR: Persistent Work Order Identity

**Status:** Accepted  
**Release:** v0.4.3

## Context

AK Labs OS requires durable engineering identity across departments, validation
runs, Historian records, artifacts, and future replay. IDs must be readable by
humans and stable enough for AI agents to reference without ambiguity.

UUIDs, timestamps, and random IDs weaken deterministic validation and make
handoffs harder to audit.

## Decision

Work Orders use deterministic sequential IDs:

```text
WO-000001
WO-000002
WO-000003
```

The Work Order sequence is persisted through the Work Order state layer. The ID
is the canonical key for Work Order lookup, transaction records, validation
evidence, and workspace ownership.

## Alternatives

- UUIDs: rejected because they are less readable and not deterministic.
- Timestamp IDs: rejected because deterministic mode must avoid timestamp-based
  identity.
- In-memory counters only: rejected because identity would not survive process
  boundaries.
- Title-derived IDs: rejected because titles can collide or change.

## Consequences

- Work Orders are easy to reference in handoffs.
- Validation can assert deterministic identity behavior.
- ETP can link transactions to one stable Work Order ID.
- Historian records can reconstruct lifecycle and ownership history by ID.
- Sequence allocation must remain controlled by the Work Order identity layer.

## Related Files

- `work_orders/ids.py`
- `work_orders/state.py`
- `work_orders/state/work_order_counter.json`
- `work_orders/manager.py`
- `validation/suites/work_orders.py`
