"""
historian.py — organizational memory for AK Labs OS.

ONE job (Principle 6): turn the raw policy_log into organizational
knowledge. It does NOT execute anything, does NOT change policy.yaml,
and does NOT generate its own confidence scores.

Two things it actually does:
  1. compute_policy_stats()      -> real evidence about a policy's
                                     track record (the substrate a
                                     future evidence-based confidence
                                     score would be computed from —
                                     not a confidence score itself)
  2. detect_repeated_decisions() -> when the same policy escalates for
                                     the same reason repeatedly, surface
                                     it as a policy CANDIDATE. Candidates
                                     sit in policy_candidates as 'pending'
                                     until AK explicitly approves or
                                     rejects them. Nothing here ever
                                     edits policies.yaml — that stays a
                                     human action, on purpose (Principle 3).
"""

import sqlite3
import json
from collections import Counter
from datetime import datetime, timezone

from policy_engine import DB_PATH


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS policy_candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_ts TEXT,
            policy_id TEXT,
            pattern_description TEXT,
            occurrences INTEGER,
            suggested_change TEXT,
            status TEXT DEFAULT 'pending',
            reviewed_ts TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS engineering_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_ts TEXT,
            feature_request TEXT,
            artifact_path TEXT,
            review_path TEXT,
            verdict TEXT,
            score INTEGER,
            risk INTEGER,
            summary TEXT,
            brief_json TEXT,
            review_json TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS filesystem_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_ts TEXT,
            policy TEXT,
            severity TEXT,
            action TEXT,
            attempted_path TEXT,
            normalized_analysis TEXT,
            rejection_reason TEXT,
            originating_department TEXT,
            event_json TEXT
        )
    """)
    conn.commit()


def compute_policy_stats(policy_id: str) -> dict:
    """
    Real, measurable evidence about how a policy has actually performed —
    not an opinion, a model's or otherwise. This is what Principle 2 means
    by "evidence-driven": every number here traces back to a logged fact.
    """
    conn = _connect()
    rows = conn.execute(
        "SELECT escalated, reason FROM policy_log WHERE policy_id = ?", (policy_id,)
    ).fetchall()
    conn.close()

    total = len(rows)
    escalations = sum(1 for escalated, _ in rows if escalated)
    reasons = Counter(reason for escalated, reason in rows if escalated and reason)

    return {
        "policy_id": policy_id,
        "total_runs": total,
        "escalations": escalations,
        "escalation_rate": round(escalations / total, 3) if total else None,
        "top_escalation_reasons": reasons.most_common(3),
    }


def detect_repeated_decisions(min_occurrences: int = 3) -> list:
    """
    Scans policy_log for a policy escalating for the SAME reason
    repeatedly. Each pattern becomes one pending policy_candidate row —
    a suggestion for AK to look at, never an automatic change.
    Safe to call repeatedly: an already-pending candidate for the same
    (policy_id, reason) is not duplicated.
    """
    conn = _connect()
    rows = conn.execute(
        "SELECT policy_id, reason, COUNT(*) as n FROM policy_log "
        "WHERE escalated = 1 AND reason IS NOT NULL "
        "GROUP BY policy_id, reason HAVING n >= ?",
        (min_occurrences,),
    ).fetchall()

    surfaced = []
    for policy_id, reason, n in rows:
        last = conn.execute(
            "SELECT id, status, occurrences FROM policy_candidates "
            "WHERE policy_id=? AND pattern_description=? "
            "ORDER BY created_ts DESC LIMIT 1",
            (policy_id, reason),
        ).fetchone()

        if last:
            _, status, last_occurrences = last
            if status == "pending":
                continue  # already awaiting a decision, don't duplicate
            if status in ("approved", "rejected") and n <= last_occurrences:
                continue  # already decided, and no new evidence since then

        suggestion = (
            f"'{policy_id}' has escalated for '{reason}' {n} times. "
            f"Worth a human look: should this become a non-escalating "
            f"policy, or does the repeated escalation mean something "
            f"upstream actually needs fixing?"
        )
        conn.execute(
            "INSERT INTO policy_candidates "
            "(created_ts, policy_id, pattern_description, occurrences, suggested_change, status) "
            "VALUES (?,?,?,?,?, 'pending')",
            (datetime.now(timezone.utc).isoformat(), policy_id, reason, n, suggestion),
        )
        surfaced.append({"policy_id": policy_id, "reason": reason, "occurrences": n})

    conn.commit()
    conn.close()
    return surfaced


def review_candidates() -> list:
    """AK-facing: every candidate still awaiting a decision."""
    conn = _connect()
    rows = conn.execute(
        "SELECT id, policy_id, pattern_description, occurrences, suggested_change "
        "FROM policy_candidates WHERE status='pending' ORDER BY occurrences DESC"
    ).fetchall()
    conn.close()
    return rows


def decide_candidate(candidate_id: int, approved: bool) -> None:
    """
    Records AK's decision on a candidate. This does NOT touch
    policies.yaml — per Principle 3, editing the actual policy file
    is a deliberate human action. This just closes the loop so the
    same pattern doesn't get re-surfaced, and the decision itself
    becomes part of organizational memory.
    """
    conn = _connect()
    conn.execute(
        "UPDATE policy_candidates SET status=?, reviewed_ts=? WHERE id=?",
        ("approved" if approved else "rejected", datetime.now(timezone.utc).isoformat(), candidate_id),
    )
    conn.commit()
    conn.close()


def record_review(feature_request: str, brief: dict, artifact_path, review_path, review: dict) -> int:
    """Persist a Reviewer result as organizational memory."""
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO engineering_reviews "
        "(created_ts, feature_request, artifact_path, review_path, verdict, score, risk, summary, brief_json, review_json) "
        "VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            datetime.now(timezone.utc).isoformat(),
            feature_request,
            str(artifact_path),
            str(review_path),
            review.get("verdict"),
            int(review.get("score", 0)),
            int(review.get("risk", 0)),
            review.get("summary", ""),
            json.dumps(brief, sort_keys=True),
            json.dumps(review, sort_keys=True),
        ),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


def record_filesystem_event(event: dict) -> int:
    """Persist blocked filesystem operations as organizational memory."""
    conn = _connect()
    cur = conn.execute(
        "INSERT INTO filesystem_events "
        "(created_ts, policy, severity, action, attempted_path, normalized_analysis, rejection_reason, "
        "originating_department, event_json) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (
            event.get("timestamp") or datetime.now(timezone.utc).isoformat(),
            event.get("policy"),
            event.get("severity"),
            event.get("action"),
            event.get("attempted_path") or event.get("path"),
            event.get("normalized_analysis"),
            event.get("reason"),
            event.get("originating_department"),
            json.dumps(event, sort_keys=True),
        ),
    )
    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AK Labs OS — Historian")
    sub = parser.add_subparsers(dest="cmd")

    stats_cmd = sub.add_parser("stats", help="Evidence-based stats for a policy")
    stats_cmd.add_argument("policy_id")

    sub.add_parser("scan", help="Scan policy_log for repeated escalations, surface candidates")
    sub.add_parser("review", help="List candidates awaiting AK's decision")

    decide_cmd = sub.add_parser("decide", help="Approve or reject a candidate")
    decide_cmd.add_argument("candidate_id", type=int)
    decide_cmd.add_argument("decision", choices=["approve", "reject"])

    args = parser.parse_args()

    if args.cmd == "stats":
        print(compute_policy_stats(args.policy_id))
    elif args.cmd == "scan":
        found = detect_repeated_decisions()
        print(f"{len(found)} new candidate(s) surfaced." if found else "No new patterns.")
        for f in found:
            print(" ", f)
    elif args.cmd == "review":
        candidates = review_candidates()
        if not candidates:
            print("Nothing pending.")
        for c in candidates:
            print(f"[{c[0]}] {c[1]} — {c[2]} (seen {c[3]}x)\n    {c[4]}")
    elif args.cmd == "decide":
        decide_candidate(args.candidate_id, args.decision == "approve")
        print(f"Candidate {args.candidate_id} marked {args.decision}d.")
    else:
        parser.print_help()
