from __future__ import annotations

import re
import yaml

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import suite_main


def _load_yaml(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def run(ctx):
    checks = []
    try:
        policies = _load_yaml(ctx.repo_root / "policies.yaml")["policies"]
        checks.append(pass_check("policies_load", "policies.yaml loads", f"{len(policies)} policies"))
    except Exception as exc:
        policies = []
        checks.append(fail_check("policies_load", "policies.yaml loads", repr(exc)))

    try:
        capabilities = _load_yaml(ctx.repo_root / "capabilities.yaml")["capabilities"]
        checks.append(pass_check("capabilities_load", "capabilities.yaml loads", f"{len(capabilities)} capabilities"))
    except Exception as exc:
        capabilities = {}
        checks.append(fail_check("capabilities_load", "capabilities.yaml loads", repr(exc)))

    try:
        culture = _load_yaml(ctx.repo_root / "culture.yaml")
        checks.append(pass_check("culture_load", "culture.yaml loads", ", ".join(sorted(culture.keys()))))
    except Exception as exc:
        checks.append(fail_check("culture_load", "culture.yaml loads", repr(exc)))

    policy_ids = {policy.get("id") for policy in policies}
    if "review_generated_code" in policy_ids:
        checks.append(pass_check("review_policy_present", "Reviewer policy exists", "review_generated_code present"))
    else:
        checks.append(fail_check("review_policy_present", "Reviewer policy exists", "review_generated_code missing"))

    policy_text = (ctx.repo_root / "policies.yaml").read_text(encoding="utf-8")
    model_markers = re.findall(r"(gpt|claude|qwen|llama|groq|anthropic)", policy_text, flags=re.IGNORECASE)
    # Comments mention providers; executable params must still avoid provider/model IDs.
    executable_policy_text = "\n".join(line for line in policy_text.splitlines() if not line.strip().startswith("#"))
    executable_markers = re.findall(r"(gpt|claude|qwen|llama|groq|anthropic)", executable_policy_text, flags=re.IGNORECASE)
    if executable_markers:
        checks.append(fail_check("policies_no_model_ids", "Executable policy config contains no model/provider IDs",
                                 ", ".join(executable_markers)))
    else:
        checks.append(pass_check("policies_no_model_ids", "Executable policy config contains no model/provider IDs",
                                 "No executable provider/model markers found", {"comment_markers": model_markers}))

    env_example = ctx.repo_root / ".env.example"
    if env_example.exists():
        checks.append(pass_check("env_example_exists", ".env.example exists", str(env_example)))
    else:
        checks.append(fail_check("env_example_exists", ".env.example exists", "missing"))

    req_lines = [
        line.strip()
        for line in (ctx.repo_root / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    unpinned = [line for line in req_lines if "==" not in line]
    if unpinned:
        checks.append(fail_check("requirements_pinned", "requirements.txt pins dependencies", ", ".join(unpinned)))
    else:
        checks.append(pass_check("requirements_pinned", "requirements.txt pins dependencies", "All dependencies pinned"))

    return suite_from_checks("configuration", checks, evidence={"capabilities": sorted(capabilities.keys())})


if __name__ == "__main__":
    suite_main("configuration")

