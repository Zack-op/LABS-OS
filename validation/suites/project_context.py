from __future__ import annotations

from pathlib import Path

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import isolated, repo_module, suite_main


def run(ctx):
    checks = []
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        orchestrator.append_to_context("PROJECT_CONTEXT unicode 🚀")
        path = Path("PROJECT_CONTEXT.md")
        text = path.read_text(encoding="utf-8") if path.exists() else ""
    checks.append(pass_check("project_context_utf8_logging", "PROJECT_CONTEXT logs Unicode", text[-200:])
                  if "🚀" in text else fail_check("project_context_utf8_logging", "PROJECT_CONTEXT logs Unicode", text[-200:]))
    return suite_from_checks("project_context", checks)


if __name__ == "__main__":
    suite_main("project_context")

