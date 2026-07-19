from __future__ import annotations

import argparse

from validation.runner import run_validation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AK Labs OS Release Validation Harness")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("release", "regression", "adversarial", "dod"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--json", nargs="?", const="", default=None)
        cmd.add_argument("--markdown", nargs="?", const="", default=None)
        cmd.add_argument("--workspace", default=None)
        cmd.add_argument("--deterministic", action="store_true")
        cmd.add_argument("--fail-fast", action="store_true")
        cmd.add_argument("--profile", default="release", choices=["release", "ci", "local"])
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    _, exit_code = run_validation(args.command, args)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
