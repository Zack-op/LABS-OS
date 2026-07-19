"""
dev_tools.py — small scripted checks used to verify AK Labs OS is
wired together correctly. Not part of the pipeline itself — these
exist so you can prove each guarantee (audit trail, anti-fabrication
gate, Historian) with one plain command, regardless of which shell
your terminal is running.

Usage:
    python dev_tools.py check-log
    python dev_tools.py break-output
    python dev_tools.py simulate-escalations --count 3
"""

import argparse
import sqlite3
from pathlib import Path

from policy_engine import load_policies, evaluate, DB_PATH
from orchestrator import verify_output
from safe_artifact_writer import SafeArtifactWriter


def check_log():
    conn = sqlite3.connect(DB_PATH)
    rows = list(conn.execute("SELECT * FROM policy_log"))
    conn.close()
    if not rows:
        print("policy_log is empty — run orchestrator.py at least once first.")
        return
    for row in rows:
        print(row)


def break_output():
    policies = load_policies()
    bad = Path("output/broken_demo.py")
    bad = SafeArtifactWriter(Path.cwd(), policies).write_text(
        bad,
        "def broken(:",
        origin="dev_tools",
        overwrite=True,
    )
    result = verify_output(bad, policies)
    print("passed:", result["passed"])
    print("interrupt_level:", result["decision"]["interrupt_level"])
    print("reason:", result["decision"]["reason"])


def simulate_escalations(count: int):
    policies = load_policies()
    for _ in range(count):
        evaluate(
            "verify_output",
            {"syntax_invalid": True, "output_empty": False, "file_not_written": False},
            policies,
        )
    print(f"Logged {count} escalation(s) for verify_output. Now run: python historian.py scan")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AK Labs OS — dev/verification helpers")
    sub = parser.add_subparsers(dest="cmd")
    sub.add_parser("check-log", help="Print every row in policy_log")
    sub.add_parser("break-output", help="Feed verify_output a broken file, prove it escalates")
    sim = sub.add_parser("simulate-escalations", help="Log N repeated escalations for verify_output")
    sim.add_argument("--count", type=int, default=3)

    args = parser.parse_args()
    if args.cmd == "check-log":
        check_log()
    elif args.cmd == "break-output":
        break_output()
    elif args.cmd == "simulate-escalations":
        simulate_escalations(args.count)
    else:
        parser.print_help()
