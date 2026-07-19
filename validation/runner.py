from __future__ import annotations

import importlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from validation.contracts import ERROR, SuiteResult, ValidationContext
from validation.dod import evaluate_definition_of_done
from validation.registry import get_suite_spec, get_suite_specs
from reporters.json_reporter import write_json_report
from reporters.markdown_reporter import write_markdown_report
from reporters.release_summary import append_release_summary
from validation.versioning import recommend_version
from validation.workspace import ValidationWorkspace, prepare_reports_dir


def _now(deterministic: bool) -> str | None:
    return None if deterministic else datetime.now(timezone.utc).isoformat(timespec="seconds")


def _run_id(command: str, deterministic: bool) -> str:
    if deterministic:
        return f"deterministic-{command}"
    return datetime.now(timezone.utc).strftime(f"{command}-%Y%m%dT%H%M%SZ")


def _suite_error(suite_id: str, exc: Exception, required: bool, deterministic: bool) -> SuiteResult:
    return SuiteResult(
        suite_id=suite_id,
        status=ERROR,
        required=required,
        started_at=_now(deterministic),
        duration_ms=0,
        checks=[],
        failures=[repr(exc)],
    )


def run_validation(command: str, args) -> tuple[dict, int]:
    repo_root = Path(__file__).resolve().parents[1]
    reports_dir = prepare_reports_dir(repo_root)
    run_id = _run_id(command, args.deterministic)

    with ValidationWorkspace(repo_root, args.workspace) as workspace:
        ctx = ValidationContext(
            repo_root=repo_root,
            workspace=workspace,
            reports_dir=reports_dir,
            command=command,
            profile=args.profile,
            deterministic=args.deterministic,
        )
        suites = []
        for spec in get_suite_specs(command):
            started = _now(args.deterministic)
            t0 = time.perf_counter()
            try:
                module = importlib.import_module(spec.module)
                result = module.run(ctx)
                result.required = spec.required
                result.started_at = started
                result.duration_ms = 0 if args.deterministic else int((time.perf_counter() - t0) * 1000)
            except Exception as exc:
                result = _suite_error(spec.suite_id, exc, spec.required, args.deterministic)
            suites.append(result.to_dict())
            if args.fail_fast and result.required and result.status != "PASS":
                break

        dod = evaluate_definition_of_done(suites)
        overall_status = "PASS" if dod["status"] == "PASS" else "FAIL"
        exit_code = 0 if overall_status == "PASS" else 1
        version = recommend_version(repo_root, dod, suites)
        artifacts = [artifact for suite in suites for artifact in suite.get("artifacts", [])]
        report = {
            "schema_version": "1.0",
            "project": "AK Labs OS",
            "validation_version": "v0.3.0",
            "run_id": run_id,
            "command": command,
            "profile": args.profile,
            "deterministic": args.deterministic,
            "overall_status": overall_status,
            "exit_code": exit_code,
            "version_recommendation": version,
            "definition_of_done": dod,
            "environment": {
                "python_version": sys.version.split()[0],
                "platform": platform.platform(),
                "has_groq_key": bool(os.environ.get("GROQ_API_KEY")),
                "has_anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
                "workspace": str(workspace),
            },
            "suites": suites,
            "artifacts": artifacts,
            "summary": {
                "passed": sum(1 for suite in suites if suite["status"] == "PASS"),
                "failed": sum(1 for suite in suites if suite["status"] == "FAIL"),
                "not_tested": sum(1 for suite in suites if suite["status"] == "NOT_TESTED"),
                "warnings": sum(len(suite.get("warnings", [])) for suite in suites),
            },
        }

        json_latest = Path(args.json) if args.json else reports_dir / "latest.json"
        md_latest = Path(args.markdown) if args.markdown else reports_dir / "latest.md"
        json_history = reports_dir / "history" / f"{run_id}.json"
        md_history = reports_dir / "history" / f"{run_id}.md"
        write_json_report(report, json_latest, json_history)
        write_markdown_report(report, md_latest, md_history)
        append_release_summary(repo_root, report, md_history, json_history)
        return report, exit_code


def run_suite_module_main(suite_id: str) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    reports_dir = prepare_reports_dir(repo_root)
    with ValidationWorkspace(repo_root) as workspace:
        ctx = ValidationContext(repo_root, workspace, reports_dir, suite_id, "local", deterministic=True)
        spec = get_suite_spec(suite_id)
        module = importlib.import_module(spec.module)
        result = module.run(ctx)
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=True))
        raise SystemExit(0 if result.status == "PASS" else 1)
