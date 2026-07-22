from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SuiteSpec:
    suite_id: str
    module: str
    required: bool = True

SUITES = [
    SuiteSpec("environment", "validation.suites.environment"),
    SuiteSpec("configuration", "validation.suites.configuration"),
    SuiteSpec("mock_pipeline", "validation.suites.mock_pipeline"),
    SuiteSpec("reviewer_regression", "validation.suites.reviewer_regression"),
    SuiteSpec("reviewer_adversarial", "validation.suites.reviewer_adversarial"),
    SuiteSpec("architect_normalization", "validation.suites.architect_normalization"),
    SuiteSpec("retry_fallback", "validation.suites.retry_fallback"),
    SuiteSpec("historian", "validation.suites.historian"),
    SuiteSpec("utf8_artifacts", "validation.suites.utf8_artifacts"),
    SuiteSpec("verify_gating", "validation.suites.verify_gating"),
    SuiteSpec("project_context", "validation.suites.project_context"),
    SuiteSpec("filesystem_safety", "validation.suites.filesystem_safety"),
    SuiteSpec("work_orders", "validation.suites.work_orders"),
    SuiteSpec("etp_integration", "validation.suites.etp_integration"),
]

COMMAND_SUITES = {
    "release": [spec.suite_id for spec in SUITES],
    "regression": [
        "reviewer_regression",
        "architect_normalization",
        "retry_fallback",
        "historian",
        "utf8_artifacts",
        "verify_gating",
        "project_context",
        "work_orders",
        "etp_integration",
    ],
    "adversarial": ["reviewer_adversarial"],
    "dod": [spec.suite_id for spec in SUITES],
}

def get_suite_specs(command: str) -> list[SuiteSpec]:
    wanted = set(COMMAND_SUITES[command])
    return [spec for spec in SUITES if spec.suite_id in wanted]

def get_suite_spec(suite_id: str) -> SuiteSpec:
    for spec in SUITES:
        if spec.suite_id == suite_id:
            return spec
    raise KeyError(f"Unknown suite: {suite_id}")