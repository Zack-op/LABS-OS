from __future__ import annotations

from pathlib import Path

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import isolated, policies, repo_module, sqlite_rows, suite_main


def _structured_block_check(check_id: str, expected: str, exc: Exception, evidence: dict | None = None):
    event = getattr(exc, "event", None)
    if isinstance(event, dict) and event.get("action") == "BLOCKED" and event.get("policy") == "filesystem_safety":
        return pass_check(check_id, expected, f"blocked: {event.get('reason_code')}", event)
    data = {"exception": repr(exc)}
    if evidence:
        data.update(evidence)
    return fail_check(check_id, expected, "blocked without structured filesystem event", data)


def _expect_title_blocked(ctx, title: str, check_id: str):
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        try:
            result = orchestrator.developer_generate_code({"title": title}, policies(ctx), mock=True)
        except Exception as exc:
            return _structured_block_check(check_id, "Unsafe output title is blocked", exc, {"title": title})
        path = Path(result["path"])
        return fail_check(check_id, "Unsafe output title is blocked", f"not blocked: {path}", {"title": title, "path": str(path)})


def _expect_writer_blocked(ctx, relative_path: str, check_id: str, expected: str):
    with isolated(ctx):
        writer_mod = repo_module("safe_artifact_writer")
        writer = writer_mod.SafeArtifactWriter(Path.cwd(), policies(ctx))
        try:
            writer.write_text(relative_path, "unsafe", origin="filesystem_safety_suite")
        except Exception as exc:
            return _structured_block_check(check_id, expected, exc, {"path": relative_path})
        return fail_check(check_id, expected, "write was allowed", {"path": relative_path})


def run(ctx):
    checks = [
        _expect_title_blocked(ctx, "../traversal", "traversal_blocked"),
        _expect_title_blocked(ctx, "C:\\Windows\\System32\\drivers\\etc\\hosts", "absolute_path_blocked"),
        _expect_title_blocked(ctx, "recursive/path/name", "recursive_path_blocked"),
        _expect_title_blocked(ctx, '<>:"|?*', "invalid_filename_blocked"),
        _expect_title_blocked(ctx, "CON", "reserved_filename_blocked"),
        _expect_writer_blocked(ctx, "policies.yaml", "protected_files_blocked", "Protected project files are blocked"),
        _expect_writer_blocked(ctx, str(ctx.repo_root / "outside_workspace.py"), "workspace_isolation_enforced",
                               "Writes outside approved workspace are blocked"),
    ]
    with isolated(ctx):
        orchestrator = repo_module("orchestrator")
        try:
            first = orchestrator.developer_generate_code({"title": "duplicate output folder"}, policies(ctx), mock=True)
            second = orchestrator.developer_generate_code({"title": "duplicate output folder"}, policies(ctx), mock=True)
            if Path(first["path"]) != Path(second["path"]):
                checks.append(pass_check("duplicate_output_blocked", "Duplicate output paths are blocked or made unique", f"{first['path']} != {second['path']}"))
            else:
                checks.append(fail_check("duplicate_output_blocked", "Duplicate output paths are blocked or made unique", f"same path: {first['path']}"))
        except Exception as exc:
            checks.append(_structured_block_check(
                "duplicate_output_blocked",
                "Duplicate output paths are blocked or made unique",
                exc,
            ))

        policy_rows = sqlite_rows(Path("ak_labs_os.db"), "SELECT policy_id, escalated FROM policy_log WHERE policy_id='filesystem_safety'")
        event_rows = sqlite_rows(
            Path("ak_labs_os.db"),
            "SELECT policy, action, attempted_path, rejection_reason FROM filesystem_events WHERE policy='filesystem_safety'",
        )
        checks.append(pass_check("blocked_policy_event_logged", "Blocked writes create policy events", str(policy_rows))
                      if any(row[0] == "filesystem_safety" and row[1] == 1 for row in policy_rows)
                      else fail_check("blocked_policy_event_logged", "Blocked writes create policy events", str(policy_rows)))
        checks.append(pass_check("blocked_historian_event_persisted", "Historian persists blocked filesystem events", str(event_rows[-3:]))
                      if event_rows else
                      fail_check("blocked_historian_event_persisted", "Historian persists blocked filesystem events", "no filesystem_events rows"))
    return suite_from_checks("filesystem_safety", checks)


if __name__ == "__main__":
    suite_main("filesystem_safety")
