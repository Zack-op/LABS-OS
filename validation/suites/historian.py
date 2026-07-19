from __future__ import annotations

import json
import sqlite3

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import BRIEF, isolated, repo_module, suite_main


def run(ctx):
    checks = []
    with isolated(ctx):
        historian = repo_module("historian")
        review = {"verdict": "FAIL", "score": 1, "risk": 9, "issues": [{"category": "utf8", "message": "emoji 🚀"}], "summary": "unicode 🚀"}
        row_id = historian.record_review("Historian 🚀", BRIEF, "artifact.py", "review.md", review)
        conn = sqlite3.connect("ak_labs_os.db")
        row = conn.execute("SELECT feature_request, verdict, score, risk, review_json FROM engineering_reviews WHERE id=?", (row_id,)).fetchone()
        conn.close()
    if row and row[0] == "Historian 🚀" and row[1] == "FAIL" and json.loads(row[4])["summary"] == "unicode 🚀":
        checks.append(pass_check("review_persistence_utf8", "Historian persists review JSON with Unicode", str(row)))
    else:
        checks.append(fail_check("review_persistence_utf8", "Historian persists review JSON with Unicode", str(row)))
    return suite_from_checks("historian", checks)


if __name__ == "__main__":
    suite_main("historian")

