from __future__ import annotations

from pathlib import Path


def _suite_notes(suite: dict) -> str:
    if suite["status"] == "PASS":
        return "All checks passed"
    if suite.get("failures"):
        return "Failed checks: " + ", ".join(suite["failures"])
    return suite["status"]


def render_markdown(report: dict) -> str:
    lines = [
        "# AK Labs OS Release Validation Report",
        "",
        "## Executive Summary",
        f"- Overall status: {report['overall_status']}",
        f"- Suggested version: {report['version_recommendation']['suggested']}",
        f"- Readiness score: {report['version_recommendation']['readiness_score']}/100",
        f"- Release recommendation: {report['version_recommendation']['reason']}",
        "",
        "## Validation Matrix",
        "| Suite | Status | Required | Notes |",
        "|---|---:|---:|---|",
    ]
    for suite in report["suites"]:
        lines.append(f"| {suite['suite_id']} | {suite['status']} | {suite['required']} | {_suite_notes(suite)} |")

    lines.extend(["", "## Definition of Done", "| Item | Status | Evidence |", "|---|---:|---|"])
    for item in report["definition_of_done"]["items"]:
        evidence = ", ".join(item.get("evidence_refs", []))
        lines.append(f"| {item['id']} | {item['status']} | {evidence} |")

    lines.extend(["", "## Critical Failures"])
    failures = [
        (suite, check)
        for suite in report["suites"]
        for check in suite["checks"]
        if check["status"] in {"FAIL", "ERROR"}
    ]
    if not failures:
        lines.append("None.")
    for suite, check in failures:
        lines.extend([
            f"### {suite['suite_id']}::{check['check_id']}",
            f"Suite: {suite['suite_id']}",
            f"Check: {check['check_id']}",
            f"Expected: {check['expected']}",
            f"Actual: {check['actual']}",
            f"Evidence: `{check['evidence']}`",
            "Suggested owner: Release Infrastructure / owning runtime component",
            "",
        ])

    lines.extend(["## Warnings"])
    warnings = [warning for suite in report["suites"] for warning in suite.get("warnings", [])]
    lines.extend(warnings or ["None."])

    lines.extend(["", "## Not Tested"])
    not_tested = [
        f"{suite['suite_id']}::{check['check_id']}"
        for suite in report["suites"]
        for check in suite["checks"]
        if check["status"] == "NOT_TESTED"
    ]
    lines.extend(not_tested or ["None."])

    for title, prefix in [
        ("Regression Results", "reviewer_regression"),
        ("Adversarial Results", "reviewer_adversarial"),
        ("Live LLM Results", "live_pipeline"),
    ]:
        lines.extend(["", f"## {title}"])
        selected = [suite for suite in report["suites"] if suite["suite_id"].startswith(prefix)]
        if not selected:
            lines.append("Not included in this command.")
        for suite in selected:
            for check in suite["checks"]:
                lines.append(f"- {check['check_id']}: {check['status']}")

    lines.extend(["", "## Artifacts"])
    for artifact in report.get("artifacts", []):
        lines.append(f"- {artifact['type']}: `{artifact['path']}`")
    if not report.get("artifacts"):
        lines.append("None.")

    lines.extend([
        "",
        "## Environment",
        f"- Python: {report['environment'].get('python_version')}",
        f"- Platform: {report['environment'].get('platform')}",
        f"- Workspace: `{report['environment'].get('workspace')}`",
        "",
        "## Version Recommendation",
        f"- Current: {report['version_recommendation']['current']}",
        f"- Suggested: {report['version_recommendation']['suggested']}",
        f"- Reason: {report['version_recommendation']['reason']}",
        "",
        "## RELEASE_SUMMARY Update",
        "Updated automatically unless report writing failed.",
        "",
    ])
    return "\n".join(lines)


def write_markdown_report(report: dict, latest_path: Path, history_path: Path) -> None:
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    payload = render_markdown(report)
    latest_path.write_text(payload, encoding="utf-8")
    history_path.write_text(payload, encoding="utf-8")
