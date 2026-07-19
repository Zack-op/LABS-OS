from __future__ import annotations

import contextlib
import importlib
import io
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Callable

import yaml

from validation.contracts import CheckResult, fail_check, pass_check


BRIEF = {
    "title": "Validation fixture",
    "in_scope": ["Run release validation"],
    "out_of_scope": ["Production changes"],
    "acceptance_criteria": ["Expected validation result is observed"],
}


@contextlib.contextmanager
def isolated(ctx):
    previous_cwd = Path.cwd()
    if str(ctx.repo_root) not in sys.path:
        sys.path.insert(0, str(ctx.repo_root))
    ctx.workspace.mkdir(parents=True, exist_ok=True)
    os.chdir(ctx.workspace)
    try:
        yield
    finally:
        os.chdir(previous_cwd)


def repo_module(name: str):
    if name in sys.modules:
        return sys.modules[name]
    return importlib.import_module(name)


def policies(ctx) -> dict:
    data = yaml.safe_load((ctx.repo_root / "policies.yaml").read_text(encoding="utf-8"))
    return {policy["id"]: policy for policy in data["policies"]}


def write_fixture(path: Path, code: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(code, encoding="utf-8")
    return path


def reviewer_check(ctx, check_id: str, code: str, expect_fail: bool,
                   expected_categories: list[str] | None = None) -> CheckResult:
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        path = write_fixture(ctx.workspace / "output" / f"{check_id}.py", code)
        review = orchestrator.review_generated_code(BRIEF, {"path": path, "code": code})
    categories = sorted({issue["category"] for issue in review["issues"]})
    expected_categories = expected_categories or []
    verdict_ok = review["verdict"] == ("FAIL" if expect_fail else "PASS")
    categories_ok = all(category in categories for category in expected_categories)
    evidence = {"verdict": review["verdict"], "categories": categories, "issues": review["issues"]}
    if verdict_ok and categories_ok:
        return pass_check(check_id, f"Reviewer verdict {'FAIL' if expect_fail else 'PASS'}", review["verdict"], evidence)
    return fail_check(check_id, f"Reviewer verdict {'FAIL' if expect_fail else 'PASS'} with {expected_categories}",
                      f"{review['verdict']} with {categories}", evidence)


def capture_stdout(fn: Callable[[], None]) -> str:
    stream = io.StringIO()
    with contextlib.redirect_stdout(stream):
        fn()
    return stream.getvalue()


def sqlite_rows(db_path: Path, query: str, params: tuple = ()) -> list:
    conn = sqlite3.connect(db_path)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def valid_work_order_json() -> str:
    return json.dumps({
        "title": "Valid",
        "in_scope": ["Do one thing"],
        "out_of_scope": ["Do not do another thing"],
        "acceptance_criteria": ["It works"],
    })


def suite_main(suite_id: str) -> None:
    from validation.runner import run_suite_module_main
    run_suite_module_main(suite_id)

