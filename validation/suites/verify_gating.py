import json
import re
from pathlib import Path
from unittest.mock import patch, MagicMock
from validation.contracts import pass_check, fail_check, suite_from_checks
from validation.suites.helpers import isolated, suite_main
import orchestrator

def _create_mock_repo(workspace: Path):
    """
    Creates a minimal physical workspace to ensure Repository Intelligence 
    and File Selection calculate positive engineering relevance, preventing 
    the pipeline from escalating early at the zero_files_matched boundary.
    """
    (workspace / "backend" / "api").mkdir(parents=True, exist_ok=True)
    (workspace / "backend" / "main.py").write_text("from fastapi import FastAPI\nimport backend.api.routes", encoding="utf-8")
    (workspace / "backend" / "api" / "routes.py").write_text("def get_health(): pass", encoding="utf-8")
    (workspace / "backend" / "requirements.txt").write_text("fastapi==0.100.0", encoding="utf-8")

def run(ctx):
    checks = []
    
    # Safe tracking variables for the console summary
    reviewer_executed_pass = False
    reviewer_artifact_pass = False
    verify_skipped_pass = False
    context_logging_pass = False
    
    with isolated(ctx):
        _create_mock_repo(ctx.workspace)

        mock_verify_output = MagicMock(return_value={"passed": True, "decision": {"escalate": False}, "facts": {}})
        
        def deterministic_reviewer_failure(brief, dev_result):
            return {
                "verdict": "FAIL",
                "score": 0,
                "risk": 100,
                "issues": [
                    {
                        "category": "critical_architecture_violation", 
                        "severity": "critical", 
                        "message": "Injected architecture violation for validation gating."
                    }
                ],
                "summary": "Reviewer blocked generated code with 1 blocking issue(s)."
            }

        with patch('orchestrator.verify_output', mock_verify_output), \
             patch('orchestrator.review_generated_code', side_effect=deterministic_reviewer_failure) as mock_reviewer:
            
            try:
                # Issue a legitimate engineering prompt so File Selection passes
                orchestrator.run("Create a FastAPI health endpoint", mock=True)
            except Exception as e:
                checks.append(fail_check("pipeline_execution", "Pipeline executes cleanly under mock", str(e)))

        # 1. Verify Gating Behavior
        if mock_reviewer.called:
            reviewer_executed_pass = True
            checks.append(pass_check("reviewer_executed", "Pipeline reached Reviewer", "Passed"))
        else:
            checks.append(fail_check("reviewer_executed", "Pipeline reached Reviewer", "Failed"))

        if not mock_verify_output.called:
            verify_skipped_pass = True
            checks.append(pass_check("verify_skipped", "Reviewer FAIL successfully gates Verify execution", "Passed"))
        else:
            checks.append(fail_check("verify_skipped", "Reviewer FAIL successfully gates Verify execution", "Verify was called despite Reviewer failure"))

        # 2. Artifact and Log Persistence Verification
        context_file = ctx.workspace / "PROJECT_CONTEXT.md"
        if context_file.exists():
            content = context_file.read_text(encoding="utf-8")
            if "FAILED at reviewer" in content and "Create a FastAPI health endpoint" in content:
                context_logging_pass = True
                checks.append(pass_check("context_logging", "Reviewer failure is correctly logged to PROJECT_CONTEXT.md", "Passed"))
            else:
                checks.append(fail_check("context_logging", "Reviewer failure is correctly logged to PROJECT_CONTEXT.md", "Log entry missing or malformed"))
        else:
            checks.append(fail_check("context_logging", "Reviewer failure is correctly logged to PROJECT_CONTEXT.md", "PROJECT_CONTEXT.md not created"))

        wo_dir = ctx.workspace / "output" / "work_orders"
        if wo_dir.exists():
            wo_folders = [d for d in wo_dir.iterdir() if d.is_dir()]
            if wo_folders:
                # Deterministically select the most recently modified Work Order workspace
                selected_wo = max(wo_folders, key=lambda d: d.stat().st_mtime)
                review_file = selected_wo / "review.md"
                
                if review_file.exists():
                    review_content = review_file.read_text(encoding="utf-8")
                    try:
                        # Assert against the canonical Reviewer contract
                        match = re.search(r"```json\s*(.*?)\s*```", review_content, re.DOTALL)
                        if match:
                            review_data = json.loads(match.group(1))
                            if review_data.get("verdict") == "FAIL":
                                reviewer_artifact_pass = True
                                checks.append(pass_check("reviewer_artifact", "Reviewer failure artifact natively reports FAIL verdict", "Passed"))
                            else:
                                checks.append(fail_check("reviewer_artifact", "Reviewer failure artifact natively reports FAIL verdict", f"Verdict was {review_data.get('verdict')}"))
                        else:
                            checks.append(fail_check("reviewer_artifact", "Reviewer failure artifact natively reports FAIL verdict", "Valid JSON block not found in review.md"))
                    except Exception as e:
                        checks.append(fail_check("reviewer_artifact", "Reviewer failure artifact natively reports FAIL verdict", f"Failed to parse artifact JSON: {str(e)}"))
                else:
                    checks.append(fail_check("reviewer_artifact", "Reviewer failure artifact is correctly persisted to the WO workspace", "review.md missing from WO workspace"))
            else:
                checks.append(fail_check("reviewer_artifact", "Reviewer failure artifact is correctly persisted to the WO workspace", "No Work Order folder instantiated"))
        else:
            checks.append(fail_check("reviewer_artifact", "Reviewer failure artifact is correctly persisted to the WO workspace", "output/work_orders directory missing"))

    # 3. Formatted Console Output
    suite_passed = reviewer_executed_pass and reviewer_artifact_pass and verify_skipped_pass and context_logging_pass
    
    print("\n====================================================")
    print("verify_gating")
    print()
    print(f"Pipeline reached Reviewer       {'PASS' if reviewer_executed_pass else 'FAIL'}")
    print(f"Reviewer failed                 {'PASS' if reviewer_artifact_pass else 'FAIL'}")
    print(f"Verify skipped                  {'PASS' if verify_skipped_pass else 'FAIL'}")
    print(f"Pipeline terminated correctly   {'PASS' if context_logging_pass else 'FAIL'}")
    print()
    print(f"Suite Result                    {'PASS' if suite_passed else 'FAIL'}")
    print("====================================================\n")

    return suite_from_checks("verify_gating", checks)

if __name__ == "__main__":
    suite_main("verify_gating")