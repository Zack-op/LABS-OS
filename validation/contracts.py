from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PASS = "PASS"
FAIL = "FAIL"
PARTIAL = "PARTIAL"
NOT_TESTED = "NOT_TESTED"
ERROR = "ERROR"


@dataclass
class Artifact:
    type: str
    path: str
    description: str = ""
    sha256: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "path": self.path,
            "sha256": self.sha256,
            "description": self.description,
        }


@dataclass
class CheckResult:
    check_id: str
    status: str
    expected: str
    actual: str
    evidence: dict[str, Any] = field(default_factory=dict)
    artifact_paths: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "status": self.status,
            "expected": self.expected,
            "actual": self.actual,
            "evidence": self.evidence,
            "artifact_paths": self.artifact_paths,
        }


@dataclass
class SuiteResult:
    suite_id: str
    status: str
    required: bool = True
    started_at: str | None = None
    duration_ms: int = 0
    checks: list[CheckResult] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    evidence: dict[str, Any] = field(default_factory=dict)
    failures: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "suite_id": self.suite_id,
            "status": self.status,
            "required": self.required,
            "started_at": self.started_at,
            "duration_ms": self.duration_ms,
            "checks": [check.to_dict() for check in self.checks],
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "evidence": self.evidence,
            "failures": self.failures,
            "warnings": self.warnings,
        }


@dataclass
class ValidationContext:
    repo_root: Path
    workspace: Path
    reports_dir: Path
    command: str
    profile: str
    deterministic: bool = False

    def artifact_path(self, *parts: str) -> Path:
        path = self.workspace.joinpath(*parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


def pass_check(check_id: str, expected: str, actual: str, evidence: dict[str, Any] | None = None,
               artifacts: list[str] | None = None) -> CheckResult:
    return CheckResult(check_id, PASS, expected, actual, evidence or {}, artifacts or [])


def fail_check(check_id: str, expected: str, actual: str, evidence: dict[str, Any] | None = None,
               artifacts: list[str] | None = None) -> CheckResult:
    return CheckResult(check_id, FAIL, expected, actual, evidence or {}, artifacts or [])


def not_tested_check(check_id: str, expected: str, actual: str, evidence: dict[str, Any] | None = None) -> CheckResult:
    return CheckResult(check_id, NOT_TESTED, expected, actual, evidence or {}, [])


def suite_from_checks(suite_id: str, checks: list[CheckResult], required: bool = True,
                      artifacts: list[Artifact] | None = None,
                      evidence: dict[str, Any] | None = None,
                      warnings: list[str] | None = None,
                      started_at: str | None = None,
                      duration_ms: int = 0) -> SuiteResult:
    failures = [check.check_id for check in checks if check.status in {FAIL, ERROR}]
    if failures:
        status = FAIL
    elif any(check.status == NOT_TESTED for check in checks):
        status = PARTIAL
    else:
        status = PASS
    return SuiteResult(
        suite_id=suite_id,
        status=status,
        required=required,
        started_at=started_at,
        duration_ms=duration_ms,
        checks=checks,
        artifacts=artifacts or [],
        evidence=evidence or {},
        failures=failures,
        warnings=warnings or [],
    )

