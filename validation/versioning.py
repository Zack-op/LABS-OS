from __future__ import annotations

import re
from pathlib import Path

TARGET_RELEASE_VERSION = "v0.4.1-alpha"


def current_version(repo_root: Path) -> str:
    summary = repo_root / "RELEASE_SUMMARY.md"
    if not summary.exists():
        return "v0.0.0"
    text = summary.read_text(encoding="utf-8")
    match = re.search(r"Suggested version:\s*(\S+)", text)
    return match.group(1) if match else "v0.0.0"


def readiness_score(dod: dict, suites: list[dict]) -> int:
    items = dod.get("items", [])
    if not items:
        return 0
    passed = sum(1 for item in items if item["status"] == "PASS")
    raw = round((passed / len(items)) * 100)
    if dod.get("status") != "PASS":
        return min(raw, 79)
    return raw


def recommend_version(repo_root: Path, dod: dict, suites: list[dict]) -> dict:
    current = current_version(repo_root)
    score = readiness_score(dod, suites)
    if dod.get("status") == "PASS":
        suggested = TARGET_RELEASE_VERSION
        reason = "All required v0.4.1 release validation gates passed."
    else:
        suggested = current
        failed = [suite["suite_id"] for suite in suites if suite["required"] and suite["status"] != "PASS"]
        reason = "Release blocked by required validation gate(s): " + ", ".join(failed)
    return {
        "current": current,
        "suggested": suggested,
        "readiness_score": score,
        "reason": reason,
    }
