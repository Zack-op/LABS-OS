# AK Labs OS Release Validation Report

## Executive Summary
- Overall status: FAIL
- Suggested version: v0.0.0
- Readiness score: 65/100
- Release recommendation: Release blocked by required validation gate(s): mock_pipeline, utf8_artifacts, filesystem_safety, etp_integration, repo_intelligence, file_selection

## Validation Matrix
| Suite | Status | Required | Notes |
|---|---:|---:|---|
| environment | PASS | True | All checks passed |
| configuration | PASS | True | All checks passed |
| mock_pipeline | FAIL | True | Failed checks: mock_pipeline_completed, mock_output_written, mock_review_artifact_written, mock_context_logged, mock_policy_log_updated |
| reviewer_regression | PASS | True | All checks passed |
| reviewer_adversarial | PASS | True | All checks passed |
| architect_normalization | PASS | True | All checks passed |
| retry_fallback | PASS | True | All checks passed |
| historian | PASS | True | All checks passed |
| utf8_artifacts | ERROR | True | Failed checks: TypeError("developer_generate_code() missing 1 required positional argument: 'wo_id'") |
| verify_gating | PASS | True | All checks passed |
| project_context | PASS | True | All checks passed |
| filesystem_safety | FAIL | True | Failed checks: traversal_blocked, absolute_path_blocked, recursive_path_blocked, invalid_filename_blocked, reserved_filename_blocked, duplicate_output_blocked |
| work_orders | PASS | True | All checks passed |
| etp_integration | FAIL | True | Failed checks: etp_clean_run, etp_linkage, etp_rejected_run |
| repo_intelligence | ERROR | True | Failed checks: ImportError("cannot import name 'AssetClass' from 'repository_intelligence' (D:\\ak_labs_os\\repository_intelligence\\__init__.py)") |
| file_selection | FAIL | True | Failed checks: integration_dependency_expansion |
| context_builder | PASS | True | All checks passed |

## Definition of Done
| Item | Status | Evidence |
|---|---:|---|
| environment_gate | PASS |  |
| configuration_gate | PASS |  |
| mock_pipeline_gate | FAIL | C:\Users\ajagg\AppData\Local\Temp\ak_labs_validation_a9r86ehy\mock_pipeline\stdout.txt |
| reviewer_regression_gate | PASS |  |
| reviewer_adversarial_gate | PASS |  |
| architect_normalization_gate | PASS |  |
| retry_fallback_gate | PASS |  |
| historian_gate | PASS |  |
| utf8_artifacts_gate | FAIL |  |
| verify_gating_gate | PASS |  |
| project_context_gate | PASS |  |
| filesystem_safety_gate | FAIL |  |
| work_orders_gate | PASS |  |
| etp_integration_gate | FAIL |  |
| repo_intelligence_gate | FAIL |  |
| file_selection_gate | FAIL |  |
| context_builder_gate | PASS |  |

## Critical Failures
### mock_pipeline::mock_pipeline_completed
Suite: mock_pipeline
Check: mock_pipeline_completed
Expected: Mock pipeline reaches Done
Actual: 
>> Feature request: Build a function that validates an email address
>> Mode: --mock (no API calls, free)

[1/8] Architect: compiling scope...

[2/8] Repository Intelligence: scanning...

[3/8] File Selection: computing relevance...
  STOP [approval] — file_selection escalated: zero_files_matched OR low_rule_coverage OR conflicting_rules

Evidence: `{}`
Suggested owner: Release Infrastructure / owning runtime component

### mock_pipeline::mock_output_written
Suite: mock_pipeline
Check: mock_output_written
Expected: Generated output file exists
Actual: missing
Evidence: `{}`
Suggested owner: Release Infrastructure / owning runtime component

### mock_pipeline::mock_review_artifact_written
Suite: mock_pipeline
Check: mock_review_artifact_written
Expected: Review artifact exists
Actual: missing
Evidence: `{}`
Suggested owner: Release Infrastructure / owning runtime component

### mock_pipeline::mock_context_logged
Suite: mock_pipeline
Check: mock_context_logged
Expected: PROJECT_CONTEXT records shipped result
Actual: missing
Evidence: `{}`
Suggested owner: Release Infrastructure / owning runtime component

### mock_pipeline::mock_policy_log_updated
Suite: mock_pipeline
Check: mock_policy_log_updated
Expected: Policy log contains pipeline decisions
Actual: scope_compile, file_selection
Evidence: `{}`
Suggested owner: Release Infrastructure / owning runtime component

### filesystem_safety::traversal_blocked
Suite: filesystem_safety
Check: traversal_blocked
Expected: Unsafe output title is blocked
Actual: blocked without structured filesystem event
Evidence: `{'exception': 'TypeError("developer_generate_code() missing 1 required positional argument: \'wo_id\'")', 'title': '../traversal'}`
Suggested owner: Release Infrastructure / owning runtime component

### filesystem_safety::absolute_path_blocked
Suite: filesystem_safety
Check: absolute_path_blocked
Expected: Unsafe output title is blocked
Actual: blocked without structured filesystem event
Evidence: `{'exception': 'TypeError("developer_generate_code() missing 1 required positional argument: \'wo_id\'")', 'title': 'C:\\Windows\\System32\\drivers\\etc\\hosts'}`
Suggested owner: Release Infrastructure / owning runtime component

### filesystem_safety::recursive_path_blocked
Suite: filesystem_safety
Check: recursive_path_blocked
Expected: Unsafe output title is blocked
Actual: blocked without structured filesystem event
Evidence: `{'exception': 'TypeError("developer_generate_code() missing 1 required positional argument: \'wo_id\'")', 'title': 'recursive/path/name'}`
Suggested owner: Release Infrastructure / owning runtime component

### filesystem_safety::invalid_filename_blocked
Suite: filesystem_safety
Check: invalid_filename_blocked
Expected: Unsafe output title is blocked
Actual: blocked without structured filesystem event
Evidence: `{'exception': 'TypeError("developer_generate_code() missing 1 required positional argument: \'wo_id\'")', 'title': '<>:"|?*'}`
Suggested owner: Release Infrastructure / owning runtime component

### filesystem_safety::reserved_filename_blocked
Suite: filesystem_safety
Check: reserved_filename_blocked
Expected: Unsafe output title is blocked
Actual: blocked without structured filesystem event
Evidence: `{'exception': 'TypeError("developer_generate_code() missing 1 required positional argument: \'wo_id\'")', 'title': 'CON'}`
Suggested owner: Release Infrastructure / owning runtime component

### filesystem_safety::duplicate_output_blocked
Suite: filesystem_safety
Check: duplicate_output_blocked
Expected: Duplicate output paths are blocked or made unique
Actual: blocked without structured filesystem event
Evidence: `{'exception': 'TypeError("developer_generate_code() missing 1 required positional argument: \'wo_id\'")'}`
Suggested owner: Release Infrastructure / owning runtime component

### etp_integration::etp_clean_run
Suite: etp_integration
Check: etp_clean_run
Expected: Clean pipeline records 4 consecutive ACCEPTED transactions
Actual: seqs: [6, 1, 2, 3], outs: ['REJECTED', 'ACCEPTED', 'ACCEPTED', 'REJECTED']
Evidence: `{'rows': [(6, 'REJECTED', 'TX-WO-000047-005', 'TX-WO-000047-006'), (1, 'ACCEPTED', None, 'TX-WO-000048-001'), (2, 'ACCEPTED', 'TX-WO-000048-001', 'TX-WO-000048-002'), (3, 'REJECTED', 'TX-WO-000048-002', 'TX-WO-000048-003')]}`
Suggested owner: Release Infrastructure / owning runtime component

### etp_integration::etp_linkage
Suite: etp_integration
Check: etp_linkage
Expected: Pipeline transactions contain correct previous_transaction_id linkage
Actual: linkage failed
Evidence: `{'prevs': ['TX-WO-000047-005', None, 'TX-WO-000048-001', 'TX-WO-000048-002'], 'tx_ids': ['TX-WO-000047-006', 'TX-WO-000048-001', 'TX-WO-000048-002', 'TX-WO-000048-003']}`
Suggested owner: Release Infrastructure / owning runtime component

### etp_integration::etp_rejected_run
Suite: etp_integration
Check: etp_rejected_run
Expected: Failed pipeline explicitly records a REJECTED transaction
Actual: seq: 3, outcome: REJECTED, dest: Context Builder
Evidence: `{'rows': [(2, 'ACCEPTED', 'File Selection', '{"active_owner_after": "File Selection", "created_at": "2026-08-05T14:28:41+00:00", "destination_department": "File Selection", "destination_owner": "File Selection", "evidence_refs": {"completion_statement": "Repository Intelligence phase complete", "deliverable_refs": [], "policy_refs": [], "readiness_basis": "File Selection ready to receive", "review_refs": [], "validation_refs": [], "work_order_ref": "WO-000049"}, "initiated_by": "Repository Intelligence", "outcome": "ACCEPTED", "outcome_reason": "Transfer criteria met and accepted", "policy_refs": [], "previous_transaction_id": "TX-WO-000049-001", "protocol_version": "1.0", "sequence_number": 2, "source_department": "Repository Intelligence", "source_owner": "Repository Intelligence", "transaction_id": "TX-WO-000049-002", "transfer_intent": "HANDOFF", "transfer_reason": "Repository Intelligence to File Selection handoff", "validation_refs": [], "work_order_id": "WO-000049"}'), (3, 'REJECTED', 'Context Builder', '{"active_owner_after": "File Selection", "created_at": "2026-08-05T14:28:41+00:00", "destination_department": "Context Builder", "destination_owner": "Context Builder", "evidence_refs": {"completion_statement": "File Selection phase complete", "deliverable_refs": [], "policy_refs": [], "readiness_basis": "Blocked by pipeline policy", "review_refs": [], "validation_refs": [], "work_order_ref": "WO-000049"}, "initiated_by": "File Selection", "outcome": "REJECTED", "outcome_reason": "zero_files_matched OR low_rule_coverage OR conflicting_rules", "policy_refs": [], "previous_transaction_id": "TX-WO-000049-002", "protocol_version": "1.0", "sequence_number": 3, "source_department": "File Selection", "source_owner": "File Selection", "transaction_id": "TX-WO-000049-003", "transfer_intent": "HANDOFF", "transfer_reason": "File Selection to Context Builder handoff", "validation_refs": [], "work_order_id": "WO-000049"}')]}`
Suggested owner: Release Infrastructure / owning runtime component

### file_selection::integration_dependency_expansion
Suite: file_selection
Check: integration_dependency_expansion
Expected: Valid task organically expands into testing and repository dependencies
Actual: ['backend/config/settings.py', 'backend/utils/helpers.py']
Evidence: `{}`
Suggested owner: Release Infrastructure / owning runtime component

## Warnings
None.

## Not Tested
None.

## Regression Results
- sql_variable_concat: PASS
- sql_variable_percent: PASS
- sql_augassign: PASS
- command_from_import: PASS
- command_alias_shell: PASS
- os_popen: PASS
- dangerous_fs_from_import: PASS
- path_unlink: PASS
- protected_file_variable: PASS
- protected_path_open_write: PASS
- protected_file_read_only: PASS

## Adversarial Results
- plaintext_password: PASS
- missing_auth: PASS
- sql_inline_concat: PASS
- sql_variable_concat: PASS
- sql_percent: PASS
- sql_augassign: PASS
- command_direct: PASS
- command_alias: PASS
- os_popen: PASS
- dangerous_fs_direct: PASS
- dangerous_fs_alias: PASS
- path_unlink: PASS
- protected_file_write: PASS
- protected_file_open_write: PASS
- secure_parameterized: PASS

## Live LLM Results
Not included in this command.

## Artifacts
- stdout: `C:\Users\ajagg\AppData\Local\Temp\ak_labs_validation_a9r86ehy\mock_pipeline\stdout.txt`

## Environment
- Python: 3.13.14
- Platform: Windows-11-10.0.26200-SP0
- Workspace: `C:\Users\ajagg\AppData\Local\Temp\ak_labs_validation_a9r86ehy`

## Version Recommendation
- Current: v0.0.0
- Suggested: v0.0.0
- Reason: Release blocked by required validation gate(s): mock_pipeline, utf8_artifacts, filesystem_safety, etp_integration, repo_intelligence, file_selection

## RELEASE_SUMMARY Update
Updated automatically unless report writing failed.
