from __future__ import annotations

import json
from pathlib import Path


def write_json_report(report: dict, latest_path: Path, history_path: Path) -> None:
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, indent=2, ensure_ascii=True)
    latest_path.write_text(payload + "\n", encoding="utf-8")
    history_path.write_text(payload + "\n", encoding="utf-8")
