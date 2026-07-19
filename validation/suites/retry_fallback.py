from __future__ import annotations

import json
from pathlib import Path

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import isolated, policies, repo_module, suite_main, valid_work_order_json


def run(ctx):
    checks = []
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        original_call_model = orchestrator.call_model
        try:
            calls = []

            def invalid_then_valid(policy_id, task_key, prompt, policy_data, mock=False, mock_response=""):
                if task_key == "architecture":
                    calls.append(prompt)
                    return "not json" if len(calls) == 1 else valid_work_order_json()
                return mock_response

            orchestrator.call_model = invalid_then_valid
            result = orchestrator.architect_scope_compile("Retry then valid", policies(ctx), mock=True)
            ok = len(calls) == 2 and not result["used_fallback"] and len(result["invalid_logs"]) == 1
            checks.append(pass_check("retry_once_then_valid", "One retry then valid work order", str(result), {"calls": len(calls), "result": result})
                          if ok else fail_check("retry_once_then_valid", "One retry then valid work order", str(result), {"calls": len(calls), "result": result}))

            calls = []

            def always_invalid(policy_id, task_key, prompt, policy_data, mock=False, mock_response=""):
                if task_key == "architecture":
                    calls.append(prompt)
                    return "not json" if len(calls) == 1 else json.dumps({"title": "", "in_scope": []})
                return mock_response

            orchestrator.call_model = always_invalid
            result = orchestrator.architect_scope_compile("Fallback after invalid", policies(ctx), mock=True)
            logs_exist = all(Path(path).exists() for path in result["invalid_logs"]) and Path(result["fallback_log"]).exists()
            ok = len(calls) == 2 and result["used_fallback"] and logs_exist
            checks.append(pass_check("fallback_after_two_invalid", "Two invalid responses produce logged fallback", str(result), {"calls": len(calls), "result": result})
                          if ok else fail_check("fallback_after_two_invalid", "Two invalid responses produce logged fallback", str(result), {"calls": len(calls), "result": result}))
        finally:
            orchestrator.call_model = original_call_model
    return suite_from_checks("retry_fallback", checks)


if __name__ == "__main__":
    suite_main("retry_fallback")

