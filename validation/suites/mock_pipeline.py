from __future__ import annotations

from pathlib import Path

from validation.contracts import Artifact, fail_check, pass_check, suite_from_checks
from validation.suites.helpers import capture_stdout, isolated, policies, repo_module, sqlite_rows, suite_main


def run(ctx):
    checks = []
    artifacts = []
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        orchestrator.load_policies = lambda: policies(ctx)
        stdout = capture_stdout(lambda: orchestrator.run("Build a function that validates an email address", mock=True))
        stdout_path = ctx.artifact_path("mock_pipeline", "stdout.txt")
        stdout_path.write_text(stdout, encoding="utf-8")
        artifacts.append(Artifact("stdout", str(stdout_path), "Mock pipeline stdout"))

        output_path = Path("output/build_a_function_that_validates_an_email.py")
        review_path = Path("output/build_a_function_that_validates_an_email_review.md")
        context_path = Path("PROJECT_CONTEXT.md")
        db_path = Path("ak_labs_os.db")

        checks.append(pass_check("mock_pipeline_completed", "Mock pipeline reaches Done",
                                 "Done present" if "Done. AK gets" in stdout else "Done missing")
                      if "Done. AK gets" in stdout else
                      fail_check("mock_pipeline_completed", "Mock pipeline reaches Done", stdout[-500:]))
        checks.append(pass_check("mock_output_written", "Generated output file exists", str(output_path))
                      if output_path.exists() else fail_check("mock_output_written", "Generated output file exists", "missing"))
        checks.append(pass_check("mock_review_artifact_written", "Review artifact exists", str(review_path))
                      if review_path.exists() else fail_check("mock_review_artifact_written", "Review artifact exists", "missing"))
        checks.append(pass_check("mock_context_logged", "PROJECT_CONTEXT records shipped result", context_path.read_text(encoding="utf-8")[-300:])
                      if context_path.exists() and "SHIPPED" in context_path.read_text(encoding="utf-8")
                      else fail_check("mock_context_logged", "PROJECT_CONTEXT records shipped result", "missing"))
        rows = sqlite_rows(db_path, "SELECT policy_id FROM policy_log ORDER BY ts") if db_path.exists() else []
        policy_ids = [row[0] for row in rows]
        expected = {"scope_compile", "review_generated_code", "verify_output"}
        checks.append(pass_check("mock_policy_log_updated", "Policy log contains pipeline decisions", ", ".join(policy_ids))
                      if expected.issubset(set(policy_ids))
                      else fail_check("mock_policy_log_updated", "Policy log contains pipeline decisions", ", ".join(policy_ids)))

    return suite_from_checks("mock_pipeline", checks, artifacts=artifacts)


if __name__ == "__main__":
    suite_main("mock_pipeline")

