# ADR: Work Order Workspace Ownership

**Status:** Accepted  
**Release:** v0.4.3

## Context

Generated artifacts need a deterministic home that can be audited by Work
Order, transaction, validation, and Historian records. Earlier output layouts
were too loose for a persistent engineering organization because artifacts
could be treated as unrelated files instead of evidence attached to a specific
engineering task.

## Decision

Work Order artifacts use the canonical workspace layout:

```text
output/
  work_orders/
    WO-000001/
```

The Work Order owns the workspace identity. Safe Artifact Writer remains the
only approved filesystem mutation mechanism for creating, modifying, renaming,
or deleting artifacts inside that workspace.

## Alternatives

- Flat `output/` artifacts: rejected because artifact ownership is ambiguous.
- Timestamped run folders: rejected because deterministic mode must avoid
  timestamp-derived workspace identity.
- Department-owned workspaces: rejected because artifacts belong to the Work
  Order lifecycle, not a transient department stage.
- Orchestrator-owned workspaces: rejected because Orchestrator owns workflow
  coordination only.

## Consequences

- Artifacts can be traced to one Work Order.
- ETP transfer records can reference stable deliverable paths.
- Historian can reconstruct the artifact lifecycle for each Work Order.
- Validation can assert workspace isolation.
- Safe Artifact Writer continues to enforce filesystem safety and protected
  file rules.

## Related Files

- `work_orders/`
- `safe_artifact_writer.py`
- `etp/`
- `historian.py`
- `validation/suites/work_orders.py`
- `validation/suites/filesystem_safety.py`
