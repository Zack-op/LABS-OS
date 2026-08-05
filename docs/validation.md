# Validation

**Current release:** v0.4.3  
**Validation status:** GREEN after the v0.4.3 validation campaign  
**Harness location:** `validation/`

The Release Validation Harness is independent infrastructure. It validates AK
Labs OS from outside the runtime pipeline and produces deterministic evidence.

## CLI

```powershell
python -m validation.cli release --deterministic
python -m validation.cli regression --deterministic
python -m validation.cli adversarial --deterministic
python -m validation.cli dod --deterministic
```

Supported options:

- `--json`
- `--markdown`
- `--workspace`
- `--deterministic`
- `--fail-fast`
- `--profile`

## Reports

Generated reports:

- `reports/latest.json`
- `reports/latest.md`
- `reports/history/`

The JSON report is the machine-readable contract. The Markdown report is the
human-readable release handoff.

## Registered Suites

The v0.4.3 validation registry includes:

- `environment`
- `configuration`
- `mock_pipeline`
- `reviewer_regression`
- `reviewer_adversarial`
- `architect_normalization`
- `retry_fallback`
- `historian`
- `utf8_artifacts`
- `verify_gating`
- `project_context`
- `filesystem_safety`
- `work_orders`
- `etp_integration`
- `repo_intelligence`
- `file_selection`
- `context_builder`

## Release Gates

The Definition of Done requires every required suite in the selected command to
pass. A required suite that returns anything other than `PASS` fails the gate.

Release commands:

- `release`: complete release validation
- `regression`: known defect regression protection
- `adversarial`: hostile Reviewer/security cases
- `dod`: Definition-of-Done enforcement over required gates

## Regression Philosophy

Every discovered defect should become a permanent regression test when the
defect is meaningful to release quality.

Regression tests must:

- preserve the failing behavior as a reproducible case
- verify the smallest required fix
- avoid weakening validation
- run deterministically
- produce evidence in reports when possible

## Adversarial Philosophy

Adversarial suites attempt to break release-critical behavior. Passing
adversarial validation means known hostile cases are blocked; it does not mean
the system is security-complete.

## Deterministic Guarantees

Deterministic validation should avoid:

- timestamps in expected outputs
- UUIDs
- random file names
- environment-specific paths in assertions unless explicitly normalized
- network dependency for mock-mode release gates

## Documentation-Only Changes

Documentation-only changes must not alter validation logic. Full runtime
validation may be skipped for documentation-only handoffs, but the final handoff
must explicitly state that runtime validation was not rerun.
