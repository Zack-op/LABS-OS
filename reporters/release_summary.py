from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def append_release_summary(repo_root: Path, report: dict, markdown_path: Path, json_path: Path) -> None:
    path = repo_root / "RELEASE_SUMMARY.md"
    ts = "deterministic" if report.get("deterministic") else datetime.now(timezone.utc).isoformat(timespec="seconds")
    failed = [suite["suite_id"] for suite in report["suites"] if suite["required"] and suite["status"] != "PASS"]
    section = [
        "",
        f"## Release Validation Harness Run - {ts}",
        "",
        f"- Command: `{report['command']}`",
        f"- Profile: `{report['profile']}`",
        f"- Overall status: {report['overall_status']}",
        f"- Exit code: {report['exit_code']}",
        f"- Readiness score: {report['version_recommendation']['readiness_score']}/100",
        f"- Suggested version: {report['version_recommendation']['suggested']}",
        f"- JSON report: `{json_path}`",
        f"- Markdown report: `{markdown_path}`",
    ]
    if failed:
        section.append("- Failed required suites: " + ", ".join(failed))
    else:
        section.append("- Failed required suites: none")
    section.append("")
    path.write_text(path.read_text(encoding="utf-8") + "\n".join(section) + "\n", encoding="utf-8")
