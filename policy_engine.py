"""
policy_engine.py — the decision layer for AK Labs OS.

Every time the Orchestrator wants to take an action, it asks this
engine one question: proceed automatically, or stop and ask AK?

No framework, no heavy deps: PyYAML + sqlite3 (stdlib) only.
Drop this next to your existing orchestrator and PROJECT_CONTEXT.md.
"""

import sqlite3
import yaml
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

DB_PATH = "ak_labs_os.db"          # reuse your existing WAL db
POLICIES_PATH = "policies.yaml"

REVIEW_CADENCE_DAYS = {"permanent": None, "quarterly": 90, "monthly": 30}


def load_policies(path: str = POLICIES_PATH) -> dict:
    """policies.yaml -> {policy_id: policy_dict}"""
    data = yaml.safe_load(Path(path).read_text())
    return {p["id"]: p for p in data["policies"]}


def _condition_met(escalate_if: Optional[str], facts: dict) -> bool:
    """
    Tiny, deliberately dumb boolean evaluator.
    No eval() — only looks up fact names you pass in, joined by OR.
    "tests_failed_after_retries OR result_unverifiable" + facts dict
    -> True if either fact is truthy in `facts`.
    """
    if not escalate_if or escalate_if.strip().lower() == "null":
        return False
    if escalate_if.strip().lower() == "always":
        return True
    return any(facts.get(term.strip(), False) for term in escalate_if.split(" OR "))


def evaluate(policy_id: str, facts: dict, policies: Optional[dict] = None) -> dict:
    """
    The core call. Returns:
      {"proceed": bool, "escalate": bool, "reason": str|None, "on_escalate": str|None}

    facts = live signals about the current run, e.g.
      {"tests_failed_after_retries": True}
    """
    policies = policies or load_policies()
    policy = policies[policy_id]

    escalate = _condition_met(policy.get("escalate_if"), facts)
    decision = {
        "proceed": not escalate,
        "escalate": escalate,
        "interrupt_level": policy.get("interrupt_level", "none") if escalate else "none",
        "reason": policy.get("escalate_if") if escalate else None,
        "on_escalate": policy.get("on_escalate") if escalate else None,
    }
    _log(policy_id, decision, facts)
    return decision


def _log(policy_id: str, decision: dict, facts: dict) -> None:
    """Every decision — auto or escalated — becomes an audit row."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS policy_log (
            ts TEXT, policy_id TEXT, proceeded INTEGER,
            escalated INTEGER, reason TEXT, facts TEXT
        )
    """)
    conn.execute(
        "INSERT INTO policy_log VALUES (?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), policy_id,
         int(decision["proceed"]), int(decision["escalate"]),
         decision["reason"], str(facts)),
    )
    conn.commit()
    conn.close()


def policies_due_for_review(policies: Optional[dict] = None,
                             last_reviewed: Optional[dict] = None) -> list:
    """
    Flags policies whose review_cadence has lapsed.
    last_reviewed = {policy_id: datetime}. Pull this from your own
    tracking (or add a `last_reviewed` column to policy_log) once wired up.
    """
    policies = policies or load_policies()
    last_reviewed = last_reviewed or {}
    due = []
    for pid, p in policies.items():
        days = REVIEW_CADENCE_DAYS.get(p.get("review_cadence", "permanent"))
        if days is None:
            continue
        last = last_reviewed.get(pid)
        if not last or (datetime.now(timezone.utc) - last) > timedelta(days=days):
            due.append(pid)
    return due


if __name__ == "__main__":
    policies = load_policies()

    print("Scenario 1: tests failed after retries")
    print(evaluate("run_tests_on_commit", {"tests_failed_after_retries": True}, policies))
    # -> escalate: True, AK gets notified, nothing proceeds silently

    print("\nScenario 2: tests passed clean")
    print(evaluate("run_tests_on_commit", {"tests_failed_after_retries": False}, policies))
    # -> proceed: True, no interruption

    print("\nScenario 3: production deploy always escalates")
    print(evaluate("deploy_production", {}, policies))

    print("\nScenario 4: model routing hits a deprecated model")
    print(evaluate("route_model_by_task", {"model_deprecated": True}, policies))
    # -> escalate: True but non-blocking (see on_escalate), falls back
    #    and keeps moving instead of stalling the whole pipeline

    print("\nPolicies due for review right now (none reviewed yet):")
    print(policies_due_for_review(policies))
