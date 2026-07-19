from __future__ import annotations

import ast
import importlib
import platform
import sys

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import suite_main


def run(ctx):
    checks = []
    checks.append(pass_check("python_available", "Python runtime available", sys.version.split()[0]))

    missing = []
    for module in ("yaml", "dotenv", "groq"):
        try:
            importlib.import_module(module)
        except Exception as exc:
            missing.append(f"{module}: {exc}")
    if missing:
        checks.append(fail_check("dependencies_importable", "Required dependencies import", "; ".join(missing)))
    else:
        checks.append(pass_check("dependencies_importable", "Required dependencies import", "yaml, dotenv, groq imported"))

    syntax_failures = []
    for path in sorted(ctx.repo_root.glob("*.py")):
        try:
            ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc:
            syntax_failures.append(f"{path.name}: {exc}")
    if syntax_failures:
        checks.append(fail_check("python_source_parses", "Top-level Python files parse", "; ".join(syntax_failures)))
    else:
        checks.append(pass_check("python_source_parses", "Top-level Python files parse", "All top-level Python files parsed"))

    return suite_from_checks("environment", checks, evidence={"platform": platform.platform()})


if __name__ == "__main__":
    suite_main("environment")

