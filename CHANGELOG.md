# Changelog

## v0.4.3 - Architecture Freeze

Status: Production-Calibrated Architecture

### Major Additions

- Repository Intelligence
- Repository Scanner
- Repository Profile
- Dependency Graph
- Module Registry
- Alias Registry
- File Selection Engine
- Engineering Context
- Context Builder
- Persistent Work Orders
- Work Order workspace ownership
- Artifact Lifecycle
- Engineering Transaction Protocol integration
- End-to-End Validation coverage

### Architectural Stabilization

- Froze the current department pipeline:

```text
Architect
  |
Repository Intelligence
  |
File Selection
  |
Context Builder
  |
Developer
  |
Reviewer
  |
Verify
  |
Historian
```

- Clarified that Orchestrator owns workflow orchestration only.
- Clarified that Repository Intelligence owns static repository knowledge, not
  file-selection decisions.
- Clarified that File Selection owns reasoning and evidence, not repository
  scanning or context packaging.
- Clarified that Context Builder owns `EngineeringContext` packaging.
- Clarified that ETP owns ownership transfer, not Work Order state or audit
  storage.
- Clarified that Work Orders own engineering task state and deterministic
  identity.
- Standardized Work Order artifact layout under
  `output/work_orders/WO-000001/`.

### Validation

- Release validation expanded to cover Work Orders, ETP integration, Repository
  Intelligence, File Selection, and Context Builder.
- Existing release gates remain in place for filesystem safety, Reviewer
  regression, adversarial review, Architect normalization, retry/fallback,
  Historian, UTF-8 artifacts, verify gating, and project-context logging.
- v0.4.3 documentation reflects GREEN validation status after PR #2 and PR #3.

### Migration Notes

- Documentation should reference `v0.4.3` as the current stable release.
- Documentation should use `output/work_orders/<work_order_id>/` as the
  canonical Work Order workspace layout.
- Future implementation work should target v0.5.0 Implementer MVP.

## Earlier Milestones

### v0.3.1 - Filesystem Safety

- Safe Artifact Writer introduced as the approved artifact mutation layer.
- Unsafe filesystem operations are rejected instead of normalized.
- Protected-file and duplicate-collision behavior is covered by validation.

### v0.4.x - Handoff-Oriented Intelligence

- Work Orders, ETP, Repository Intelligence, File Selection, Context Builder,
  Historian integration, validation framework, and workspace ownership reached
  the v0.4.3 architecture freeze.
