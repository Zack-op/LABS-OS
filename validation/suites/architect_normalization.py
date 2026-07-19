from __future__ import annotations

import json

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import isolated, repo_module, suite_main, valid_work_order_json


def _check(ctx, check_id: str, raw: str, expect_error: bool, expect_note: bool):
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        work_order, error, note = orchestrator._parse_work_order(raw)
    ok = (bool(error) == expect_error) and (bool(note) == expect_note)
    evidence = {"error": error, "note": note, "work_order": work_order}
    if ok:
        return pass_check(check_id, f"error={expect_error}, normalization_note={expect_note}", "matched", evidence)
    return fail_check(check_id, f"error={expect_error}, normalization_note={expect_note}",
                      f"error={bool(error)}, note={bool(note)}", evidence)


def run(ctx):
    valid = valid_work_order_json()
    checks = [
        _check(ctx, "exact_json", valid, False, False),
        _check(ctx, "fenced_json_normalized", "```json\n" + valid + "\n```", False, True),
        _check(ctx, "think_wrapped_final_json", "<think>draft</think>\n" + valid, False, True),
        _check(ctx, "extra_key_rejected", json.dumps({"title": "x", "in_scope": ["a"], "out_of_scope": ["b"], "acceptance_criteria": ["c"], "extra": 1}), True, False),
        _check(ctx, "missing_key_rejected", json.dumps({"title": "x", "in_scope": ["a"]}), True, False),
        _check(ctx, "invalid_list_rejected", json.dumps({"title": "x", "in_scope": [], "out_of_scope": ["b"], "acceptance_criteria": ["c"]}), True, False),
    ]
    return suite_from_checks("architect_normalization", checks)


if __name__ == "__main__":
    suite_main("architect_normalization")

