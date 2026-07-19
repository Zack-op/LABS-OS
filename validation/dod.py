from __future__ import annotations

from typing import Any

from validation.contracts import PASS


def evaluate_definition_of_done(suites: list[dict[str, Any]]) -> dict[str, Any]:
    items = []
    for suite in suites:
        item = {
            "id": f"{suite['suite_id']}_gate",
            "description": f"{suite['suite_id']} suite must pass",
            "required": bool(suite["required"]),
            "status": PASS if suite["status"] == PASS else "FAIL",
            "source_suite": suite["suite_id"],
            "evidence_refs": [
                artifact["path"]
                for artifact in suite.get("artifacts", [])
                if artifact.get("path")
            ],
        }
        items.append(item)

    required_items = [item for item in items if item["required"]]
    status = PASS if all(item["status"] == PASS for item in required_items) else "FAIL"
    return {"status": status, "items": items}

