from __future__ import annotations

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import isolated, policies, repo_module, suite_main, valid_work_order_json


def run(ctx):
    checks = []
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        original_call_model = orchestrator.call_model
        original_verify = orchestrator.verify_output
        verify_called = {"value": False}
        try:
            def fixed_model(policy_id, task_key, prompt, policy_data, mock=False, mock_response=""):
                if task_key == "architecture":
                    return valid_work_order_json()
                if task_key == "coding_routine":
                    return 'PASSWORD = "plaintext"\n\ndef login(user, password):\n    return True\n'
                if task_key == "commit_message":
                    return "feat: should not commit"
                return mock_response

            def spy_verify(path, policy_data):
                verify_called["value"] = True
                return {"passed": True, "decision": {"escalate": False}, "facts": {}}

            orchestrator.call_model = fixed_model
            orchestrator.verify_output = spy_verify
            orchestrator.load_policies = lambda: policies(ctx)
            orchestrator.run("Verify gating reviewer fail", mock=True)
        finally:
            orchestrator.call_model = original_call_model
            orchestrator.verify_output = original_verify
    checks.append(pass_check("verify_not_called_after_reviewer_fail", "Verify is skipped after Reviewer FAIL", "not called")
                  if not verify_called["value"] else
                  fail_check("verify_not_called_after_reviewer_fail", "Verify is skipped after Reviewer FAIL", "called"))
    return suite_from_checks("verify_gating", checks)


if __name__ == "__main__":
    suite_main("verify_gating")

