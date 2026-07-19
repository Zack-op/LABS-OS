from __future__ import annotations

from pathlib import Path

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import isolated, policies, repo_module, suite_main


def run(ctx):
    checks = []
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        original_call_model = orchestrator.call_model
        try:
            def unicode_model(policy_id, task_key, prompt, policy_data, mock=False, mock_response=""):
                if task_key == "coding_routine":
                    return '"""emoji 🚀"""\n\ndef rocket():\n    return "🚀"\n'
                return mock_response

            orchestrator.call_model = unicode_model
            dev = orchestrator.developer_generate_code({"title": "UTF8 Rocket"}, policies(ctx), mock=True)
            verify = orchestrator.verify_output(dev["path"], policies(ctx))
            text = Path(dev["path"]).read_text(encoding="utf-8")
        finally:
            orchestrator.call_model = original_call_model
    ok = verify["passed"] and "🚀" in text
    checks.append(pass_check("utf8_write_read_verify", "UTF-8 artifact writes, reads, and verifies", str(dev["path"]), {"verify": verify})
                  if ok else fail_check("utf8_write_read_verify", "UTF-8 artifact writes, reads, and verifies", str(verify)))
    return suite_from_checks("utf8_artifacts", checks)


if __name__ == "__main__":
    suite_main("utf8_artifacts")

