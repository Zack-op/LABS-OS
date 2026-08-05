from __future__ import annotations
import json
from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import capture_stdout, isolated, policies, repo_module, sqlite_rows, suite_main

def run(ctx):
    checks = []
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        orchestrator.load_policies = lambda: policies(ctx)
        
        # 1. Test Clean Execution (Accepted Outcomes & Linkage)
        capture_stdout(lambda: orchestrator.run("Clean Run ETP", mock=True))
        
        # Fetch the last 4 transactions, ensuring they belong to the clean run
        rows_clean = sqlite_rows("ak_labs_os.db", "SELECT sequence_number, outcome, previous_transaction_id, transaction_id FROM etp_transactions ORDER BY id DESC LIMIT 4")
        rows_clean.reverse() # Restore chronological order
        
        if len(rows_clean) == 4:
            sequences = [row[0] for row in rows_clean]
            outcomes = [row[1] for row in rows_clean]
            previous_ids = [row[2] for row in rows_clean]
            transaction_ids = [row[3] for row in rows_clean]
            
            # Verify consecutive sequence numbers
            is_consecutive = all(sequences[i] == sequences[i-1] + 1 for i in range(1, 4))
            all_accepted = all(out == "ACCEPTED" for out in outcomes)
            
            if is_consecutive and all_accepted:
                checks.append(pass_check("etp_clean_run", "Clean pipeline records 4 consecutive ACCEPTED transactions", str(sequences)))
            else:
                checks.append(fail_check("etp_clean_run", "Clean pipeline records 4 consecutive ACCEPTED transactions", f"seqs: {sequences}, outs: {outcomes}", {"rows": rows_clean}))

            # Verify transaction linkage
            linkage_ok = True
            for i in range(1, 4):
                if previous_ids[i] != transaction_ids[i-1]:
                    linkage_ok = False
            
            if linkage_ok:
                checks.append(pass_check("etp_linkage", "Pipeline transactions contain correct previous_transaction_id linkage", "linked correctly"))
            else:
                checks.append(fail_check("etp_linkage", "Pipeline transactions contain correct previous_transaction_id linkage", "linkage failed", {"prevs": previous_ids, "tx_ids": transaction_ids}))
        else:
            checks.append(fail_check("etp_clean_run", "Clean pipeline records 4 consecutive ACCEPTED transactions", f"Found {len(rows_clean)} rows", {"rows": rows_clean}))

        # 2. Test Rejected Handoff Execution
        original_developer = orchestrator.developer_generate_code
        try:
            def failing_developer(brief, policies_dict, mock_flag):
                from safe_artifact_writer import ArtifactWriteError
                # FIXED: Added 'attempted_path' to perfectly match the expected schema
                raise ArtifactWriteError({
                    "reason": "Forced Failure", 
                    "action": "BLOCKED", 
                    "policy": "filesystem_safety",
                    "attempted_path": "/mock/blocked/path.py"
                })
            
            orchestrator.developer_generate_code = failing_developer
            capture_stdout(lambda: orchestrator.run("Failed Run ETP", mock=True))
            
            # Fetch the newest 2 transactions for the failed run
            rows_failed = sqlite_rows("ak_labs_os.db", "SELECT sequence_number, outcome, destination_department, transaction_json FROM etp_transactions ORDER BY id DESC LIMIT 2")
            rows_failed.reverse() # Restore chronological order
            
            if len(rows_failed) == 2:
                # Developer failure means second transaction (Developer -> Reviewer attempt) should be REJECTED.
                seq1, outcome1, dest1, _ = rows_failed[0]
                seq2, outcome2, dest2, tx_json_str = rows_failed[1]
                
                is_consecutive_failed = (seq2 == seq1 + 1)
                
                if is_consecutive_failed and outcome2 == "REJECTED" and dest2 == "Reviewer":
                    tx_json = json.loads(tx_json_str)
                    # Ensure ownership remained unchanged
                    if tx_json["active_owner_after"] == tx_json["source_owner"]:
                        checks.append(pass_check("etp_rejected_run", "Failed pipeline explicitly records a REJECTED transaction with unchanged ownership", str((seq2, outcome2))))
                    else:
                        checks.append(fail_check("etp_rejected_run", "Failed pipeline explicitly records a REJECTED transaction with unchanged ownership", tx_json["active_owner_after"], {"tx": tx_json}))
                else:
                    checks.append(fail_check("etp_rejected_run", "Failed pipeline explicitly records a REJECTED transaction", f"seq: {seq2}, outcome: {outcome2}, dest: {dest2}", {"rows": rows_failed}))
            else:
                checks.append(fail_check("etp_rejected_run", "Failed pipeline explicitly records a REJECTED transaction", f"Found {len(rows_failed)} rows", {"rows": rows_failed}))
        finally:
            orchestrator.developer_generate_code = original_developer

    return suite_from_checks("etp_integration", checks)

if __name__ == "__main__":
    suite_main("etp_integration")