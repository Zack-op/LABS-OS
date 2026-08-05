"""
orchestrator.py — AK Labs OS, minimal working loop.

Run (free, no API calls):
    python orchestrator.py "Build a function that validates an email address" --mock

Run (real, needs GROQ_API_KEY in .env):
    python orchestrator.py "Build a function that validates an email address"

Flow:
    Architect (scope_compile) -> Repository Intelligence -> File Selection 
    -> Context Builder -> Developer (generate_code) -> Reviewer
    -> Verify (anti-fabrication gate) -> Commit message
    -> Log everything to SQLite + PROJECT_CONTEXT.md

Every stage is gated by policy_engine.evaluate(). If a stage escalates,
the pipeline stops and prints what AK needs to decide — it never
guesses its way past a stage it isn't sure about.
"""

import argparse
import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import asdict

from policy_engine import load_policies, evaluate
from llm_router import call_model
from safe_artifact_writer import ArtifactWriteError, SafeArtifactWriter
from historian import record_review, record_etp_transaction

# ETP and Work Order Integration Imports
from work_orders.models import AcceptanceCriterion, WorkOrder
from work_orders.manager import WorkOrderManager
from work_orders.enums import Department
from etp.enums import TransferIntent
from etp.tracker import ETPTracker

# HOI Integration Imports
from repository_intelligence import RepositoryScanner, RepositoryIntelligence
from file_selection import FileSelectionEngine
from context_builder import ContextBuilder, EngineeringContext

OUTPUT_DIR = Path("output")
CONTEXT_FILE = Path("PROJECT_CONTEXT.md")
ARCHITECT_LOG_DIR = OUTPUT_DIR / "architect_logs"

WORK_ORDER_KEYS = ("title", "in_scope", "out_of_scope", "acceptance_criteria")

REVIEW_WEIGHTS = {"critical": 45, "high": 30, "medium": 15, "low": 5}
REVIEW_RISK = {"critical": 10, "high": 8, "medium": 5, "low": 2}
PROTECTED_ARCHITECTURE_FILES = {
    ".env",
    "ak_labs_os.db",
    "capabilities.yaml",
    "policies.yaml",
    "PROJECT_CONTEXT.md",
}
PROTECTED_ARCHITECTURE_MODULES = {
    "capability_router",
    "historian",
    "llm_router",
    "orchestrator",
    "policy_engine",
}


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


def _strip_outer_json_fence(text: str) -> tuple[str, str | None]:
    match = re.fullmatch(r"\s*```(?:json)?\s*(.*?)\s*```\s*", text, flags=re.DOTALL)
    if match:
        return match.group(1).strip(), "raw response was wrapped in a markdown JSON fence"
    return text.strip(), None


def _extract_json(text: str) -> tuple[dict, str | None]:
    cleaned, fence_note = _strip_outer_json_fence(text)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed, fence_note
        raise ValueError("architect output must be a JSON object")
    except (json.JSONDecodeError, ValueError) as exact_error:
        normalized = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
        normalized = re.sub(r"```(?:json)?|```", "", normalized, flags=re.IGNORECASE).strip()
        decoder = json.JSONDecoder()
        candidates = []
        index = 0
        while True:
            start = normalized.find("{", index)
            if start == -1:
                break
            try:
                parsed, offset = decoder.raw_decode(normalized[start:])
            except json.JSONDecodeError:
                index = start + 1
                continue
            if isinstance(parsed, dict):
                candidates.append(parsed)
            index = start + max(offset, 1)
        if candidates:
            return candidates[-1], f"raw response was not a single JSON object: {exact_error}"
        raise


def _validate_work_order(candidate: dict) -> tuple[dict, str | None]:
    if not isinstance(candidate, dict):
        return {}, "work order must be a JSON object"

    missing = [key for key in WORK_ORDER_KEYS if key not in candidate]
    if missing:
        return {}, f"missing required key(s): {', '.join(missing)}"

    extra = sorted(set(candidate) - set(WORK_ORDER_KEYS))
    if extra:
        return {}, f"unexpected key(s): {', '.join(extra)}"

    title = candidate.get("title")
    if not isinstance(title, str) or not title.strip():
        return {}, "title must be a non-empty string"

    normalized = {"title": title.strip()}
    for key in ("in_scope", "out_of_scope", "acceptance_criteria"):
        value = candidate.get(key)
        if not isinstance(value, list) or not value:
            return {}, f"{key} must be a non-empty list"
        if not all(isinstance(item, str) and item.strip() for item in value):
            return {}, f"{key} must contain only non-empty strings"
        normalized[key] = [item.strip() for item in value]

    return normalized, None


def _parse_work_order(raw: str) -> tuple[dict, str | None, str | None]:
    try:
        parsed, normalization_note = _extract_json(raw)
    except Exception as exc:
        return {}, f"json_parse_error: {exc}", None
    work_order, validation_error = _validate_work_order(parsed)
    return work_order, validation_error, normalization_note


def _architect_prompt(feature_request: str, retry_error: str | None = None) -> str:
    retry_clause = ""
    if retry_error:
        retry_clause = (
            "The previous response was invalid and was rejected. "
            f"Validation error: {retry_error}\n"
            "Retry exactly once with a valid work order.\n\n"
        )
    schema = {
        "title": "Short concrete work order title",
        "in_scope": ["Specific implementation task"],
        "out_of_scope": ["Explicitly excluded work"],
        "acceptance_criteria": ["Observable pass/fail criterion"],
    }
    return (
        f"{retry_clause}"
        "You are the Architect department for AK Labs OS. Produce one structured work order.\n"
        "Return exactly one raw JSON object. Do not include markdown fences, prose, comments, "
        "reasoning, <think> blocks, or text before/after the object.\n"
        "The object must contain exactly these keys: title, in_scope, out_of_scope, acceptance_criteria.\n"
        "All list fields must be non-empty lists of non-empty strings.\n\n"
        f"Schema example:\n{json.dumps(schema, indent=2)}\n\n"
        f"Feature request: {feature_request}"
    )


def _fallback_work_order(feature_request: str) -> dict:
    title = feature_request.strip() or "Generated Feature"
    return {
        "title": title,
        "in_scope": [f"Implement exactly this request: {title}"],
        "out_of_scope": [
            "Anything not explicitly required by the feature request",
            "External services, persistence, deployment, or UI unless explicitly requested",
        ],
        "acceptance_criteria": [
            "Generated artifact is written to disk",
            "Generated artifact passes Reviewer",
            "Generated artifact parses as valid Python",
            f"Implementation directly addresses: {title}",
        ],
    }


def _write_architect_log(
    feature_request: str,
    attempt: int,
    raw_output: str,
    validation_error: str,
    status: str,
    work_order: dict | None = None,
    policies: dict | None = None,
) -> Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = slugify(feature_request) or "feature"
    path = ARCHITECT_LOG_DIR / f"{slug}_attempt_{attempt}_{status}_{ts}.json"
    payload = {
        "created_ts": datetime.now(timezone.utc).isoformat(),
        "feature_request": feature_request,
        "attempt": attempt,
        "status": status,
        "validation_error": validation_error,
        "raw_output": raw_output,
        "work_order": work_order,
    }
    SafeArtifactWriter(Path.cwd(), policies).write_text(
        path,
        json.dumps(payload, indent=2, ensure_ascii=True),
        origin="architect",
    )
    return path


def architect_scope_compile(feature_request: str, policies: dict, mock: bool) -> dict:
    mock_response = json.dumps({
        "title": feature_request,
        "in_scope": [f"Implement: {feature_request}"],
        "out_of_scope": ["Anything not explicitly listed above"],
        "acceptance_criteria": ["Code parses", "Function is callable", "Has a docstring"],
    })
    invalid_logs = []
    normalization_logs = []
    retry_error = None

    for attempt in (1, 2):
        raw = call_model(
            "route_model_by_task",
            "architecture",
            _architect_prompt(feature_request, retry_error),
            policies,
            mock=mock,
            mock_response=mock_response,
        )
        brief, validation_error, normalization_note = _parse_work_order(raw)
        if normalization_note:
            path = _write_architect_log(
                feature_request,
                attempt,
                raw,
                normalization_note,
                "normalized",
                brief if not validation_error else None,
                policies,
            )
            normalization_logs.append(str(path))
        if not validation_error:
            decision = evaluate(
                "scope_compile",
                {
                    "brief_empty_or_invalid": False,
                    "used_fallback": False,
                    "malformed_attempts": len(invalid_logs),
                    "normalization_logs": normalization_logs,
                    "invalid_logs": invalid_logs,
                },
                policies,
            )
            return {
                "brief": brief,
                "decision": decision,
                "used_fallback": False,
                "invalid_logs": invalid_logs,
                "normalization_logs": normalization_logs,
                "validation_error": None,
            }

        path = _write_architect_log(
            feature_request,
            attempt,
            raw,
            validation_error,
            "invalid",
            policies=policies,
        )
        invalid_logs.append(str(path))
        retry_error = validation_error

    brief = _fallback_work_order(feature_request)
    fallback_log = _write_architect_log(
        feature_request,
        len(invalid_logs) + 1,
        "",
        retry_error or "architect output invalid after retry",
        "fallback",
        brief,
        policies,
    )
    decision = evaluate(
        "scope_compile",
        {
            "brief_empty_or_invalid": False,
            "used_fallback": True,
            "malformed_attempts": len(invalid_logs),
            "normalization_logs": normalization_logs,
            "invalid_logs": invalid_logs,
            "fallback_log": str(fallback_log),
        },
        policies,
    )
    return {
        "brief": brief,
        "decision": decision,
        "used_fallback": True,
        "invalid_logs": invalid_logs,
        "normalization_logs": normalization_logs,
        "fallback_log": str(fallback_log),
        "validation_error": retry_error,
    }


def developer_generate_code(payload, policies: dict, mock: bool, wo_id: str) -> dict:
    if isinstance(payload, dict):
        summary = payload.get("title", "generated module")
        context_dict = payload
    else:
        summary = payload.summary
        context_dict = asdict(payload)
        
    prompt = (
        "You are a developer. Write a single self-contained Python module implementing "
        "ONLY what's in scope below. Include a docstring. Output ONLY code, no prose.\n\n"
        f"{json.dumps(context_dict, indent=2)}"
    )
    mock_code = f'"""{summary}"""\n\nimport re\n\ndef generated_func():\n    return True\n'
    code = call_model("route_model_by_task", "coding_routine", prompt, policies, mock=mock, mock_response=mock_code)
    import re
    code = re.sub(r"^```(?:python)?|```$", "", code.strip(), flags=re.MULTILINE).strip() + "\n"

    workspace_dir = OUTPUT_DIR / "work_orders" / wo_id
    workspace_dir.mkdir(parents=True, exist_ok=True)
    path = workspace_dir / "implementation.py"
    
    writer = SafeArtifactWriter(Path.cwd(), policies)
    writer.write_text(path, code, origin="developer")
    return {"code": code, "path": path}


def _call_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def _resolved_call_name(node, aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parent = _resolved_call_name(node.value, aliases)
        return f"{parent}.{node.attr}" if parent else node.attr
    return _call_name(node)


def _string_value(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _target_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _target_name(node.value)
    return ""


def _string_from_node(node, constants: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.Call) and node.args:
        call = _call_name(node.func)
        if call in {"Path", "pathlib.Path"}:
            return _string_from_node(node.args[0], constants)
    return None


def _contains_sql_text(node) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            lowered = child.value.lower()
            if any(term in lowered for term in ("select ", "insert ", "update ", "delete ", "drop ")):
                return True
    return False


def _is_dynamic_string(node) -> bool:
    if isinstance(node, ast.JoinedStr):
        return True
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "format":
        return True
    return False


def _is_protected_path(path_text: str | None) -> bool:
    if not path_text:
        return False
    normalized = path_text.replace("\\", "/").split("/")[-1]
    return normalized in PROTECTED_ARCHITECTURE_FILES


def _import_aliases(tree) -> dict[str, str]:
    aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                aliases[alias.asname or root] = root
        elif isinstance(node, ast.ImportFrom) and node.module:
            module = node.module.split(".")[0]
            for alias in node.names:
                aliases[alias.asname or alias.name] = f"{module}.{alias.name}"
    return aliases


def _review_issue(category: str, severity: str, message: str, line: int | None = None) -> dict:
    issue = {"category": category, "severity": severity, "message": message}
    if line is not None:
        issue["line"] = line
    return issue


def _looks_like_plaintext_password_name(name: str) -> bool:
    lowered = name.lower()
    return "password" in lowered and "hash" not in lowered and "digest" not in lowered


def _has_auth_check(function_node) -> bool:
    for child in ast.walk(function_node):
        if isinstance(child, ast.Compare):
            return True
        if isinstance(child, ast.Call):
            name = _call_name(child.func).lower()
            if name.endswith("compare_digest") or name.endswith("check_password"):
                return True
            if "verify" in name and ("password" in name or "credential" in name):
                return True
    return False


def _detect_ast_review_issues(tree) -> list:
    issues = []
    aliases = _import_aliases(tree)
    string_constants = {}
    dynamic_sql_vars = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = _string_value(node.value)
            for target in targets:
                name = _target_name(target)
                if name and value is not None:
                    string_constants[name] = value
                if name and _contains_sql_text(node.value) and _is_dynamic_string(node.value):
                    dynamic_sql_vars.add(name)
        elif isinstance(node, ast.AugAssign):
            name = _target_name(node.target)
            existing = string_constants.get(name)
            if name and (
                name in dynamic_sql_vars
                or (existing and _contains_sql_text(ast.Constant(existing)))
                or _contains_sql_text(node.value)
            ):
                dynamic_sql_vars.add(name)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            value = _string_value(node.value)
            if value:
                for target in targets:
                    name = _target_name(target)
                    if _looks_like_plaintext_password_name(name):
                        issues.append(_review_issue(
                            "plaintext_password",
                            "critical",
                            f"Plaintext password assigned to '{name}'.",
                            getattr(node, "lineno", None),
                        ))

        if isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                key_text = _string_value(key)
                value_text = _string_value(value)
                if key_text and value_text and _looks_like_plaintext_password_name(key_text):
                    issues.append(_review_issue(
                        "plaintext_password",
                        "critical",
                        f"Plaintext password stored under key '{key_text}'.",
                        getattr(node, "lineno", None),
                    ))

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            name = node.name.lower()
            params = {arg.arg.lower() for arg in node.args.args}
            auth_function = any(term in name for term in ("login", "authenticate", "authorize"))
            credential_params = bool(params & {"password", "credential", "credentials", "token"})
            returns_true = any(
                isinstance(child, ast.Return)
                and isinstance(child.value, ast.Constant)
                and child.value.value is True
                for child in ast.walk(node)
            )
            if (auth_function and (returns_true or not _has_auth_check(node))) \
                    or (credential_params and returns_true):
                issues.append(_review_issue(
                    "missing_authentication",
                    "critical",
                    f"Credential-handling function '{node.name}' does not perform a real authentication check.",
                    getattr(node, "lineno", None),
                ))

        if isinstance(node, ast.Call):
            name = _resolved_call_name(node.func, aliases)
            lowered = name.lower()
            first_arg = node.args[0] if node.args else None

            if lowered.endswith(".execute") and (
                isinstance(first_arg, (ast.BinOp, ast.JoinedStr))
                or (isinstance(first_arg, ast.Name) and first_arg.id in dynamic_sql_vars)
                or (isinstance(first_arg, ast.Call) and _contains_sql_text(first_arg) and _is_dynamic_string(first_arg))
            ):
                issues.append(_review_issue(
                    "sql_injection",
                    "critical",
                    "SQL query is assembled dynamically before execution.",
                    getattr(node, "lineno", None),
                ))

            if lowered in {
                "os.system",
                "subprocess.call",
                "subprocess.check_call",
                "subprocess.check_output",
                "subprocess.Popen".lower(),
                "subprocess.run",
                "os.popen",
            } or lowered in {"eval", "exec"}:
                issues.append(_review_issue(
                    "command_execution",
                    "critical",
                    f"Generated code executes commands through '{name}'.",
                    getattr(node, "lineno", None),
                ))

            if lowered in {
                "shutil.rmtree",
                "os.remove",
                "os.unlink",
                "os.rmdir",
                "os.removedirs",
                "unlink",
                "rmdir",
            } \
                    or lowered.endswith(".unlink") or lowered.endswith(".rmdir"):
                issues.append(_review_issue(
                    "dangerous_filesystem_operation",
                    "critical",
                    f"Generated code performs a destructive filesystem operation through '{name}'.",
                    getattr(node, "lineno", None),
                ))

            protected_path = None
            if isinstance(node.func, ast.Attribute) and node.func.attr == "open":
                mode = _string_from_node(node.args[0], string_constants) if node.args else ""
                if any(flag in mode for flag in ("w", "a", "x", "+")):
                    protected_path = _string_from_node(node.func.value, string_constants)
            elif lowered == "open" and node.args:
                mode = _string_from_node(node.args[1], string_constants) if len(node.args) > 1 else ""
                if any(flag in mode for flag in ("w", "a", "x", "+")):
                    protected_path = _string_from_node(node.args[0], string_constants)
            elif isinstance(node.func, ast.Attribute) and lowered.split(".")[-1] in {
                "write_text",
                "write_bytes",
                "unlink",
                "rename",
                "replace",
            }:
                protected_path = _string_from_node(node.func.value, string_constants)
            if _is_protected_path(protected_path):
                issues.append(_review_issue(
                    "critical_architecture_violation",
                    "critical",
                    f"Generated code attempts to modify protected AK Labs OS file '{protected_path}'.",
                    getattr(node, "lineno", None),
                ))

        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = []
            if isinstance(node, ast.Import):
                imported = [alias.name.split(".")[0] for alias in node.names]
            elif node.module:
                imported = [node.module.split(".")[0]]
            for module in imported:
                if module in PROTECTED_ARCHITECTURE_MODULES:
                    issues.append(_review_issue(
                        "critical_architecture_violation",
                        "critical",
                        f"Generated code imports AK Labs OS runtime module '{module}'.",
                        getattr(node, "lineno", None),
                    ))

    return issues


def _detect_text_review_issues(code: str) -> list:
    issues = []
    for line_no, line in enumerate(code.splitlines(), start=1):
        lowered = line.lower()
        if "execute(" in lowered and any(op in line for op in ("+", "%", "f\"")):
            issues.append(_review_issue(
                "sql_injection",
                "critical",
                "SQL execution line appears to assemble query text dynamically.",
                line_no,
            ))
        if "rm -rf" in lowered:
            issues.append(_review_issue(
                "dangerous_filesystem_operation",
                "critical",
                "Generated code contains recursive delete command text.",
                line_no,
            ))
        if any(name.lower() in lowered for name in PROTECTED_ARCHITECTURE_FILES) and any(
            op in lowered for op in ("write_text", "unlink", "remove", "rmtree")
        ):
            issues.append(_review_issue(
                "critical_architecture_violation",
                "critical",
                "Generated code attempts to modify protected AK Labs OS files.",
                line_no,
            ))
    return issues


def review_generated_code(brief: dict, dev_result: dict) -> dict:
    """
    Reviewer department: consumes the Architect brief, Developer result,
    and generated file contents before Verify is allowed to run.
    """
    path = Path(dev_result["path"])
    code = path.read_text(encoding="utf-8") if path.exists() else dev_result.get("code", "")
    issues = []

    if not brief.get("title"):
        issues.append(_review_issue(
            "critical_architecture_violation",
            "critical",
            "Architect brief has no title; reviewer cannot verify scope.",
        ))

    if not path.exists():
        issues.append(_review_issue(
            "critical_architecture_violation",
            "critical",
            f"Developer artifact is missing: {path}",
        ))

    try:
        tree = ast.parse(code)
        issues.extend(_detect_ast_review_issues(tree))
    except SyntaxError:
        pass

    issues.extend(_detect_text_review_issues(code))

    score = max(0, 100 - sum(REVIEW_WEIGHTS.get(i["severity"], 0) for i in issues))
    risk = max((REVIEW_RISK.get(i["severity"], 0) for i in issues), default=0)
    verdict = "FAIL" if issues else "PASS"
    summary = (
        "Reviewer passed; no blocking security or architecture issues detected."
        if verdict == "PASS"
        else f"Reviewer blocked generated code with {len(issues)} blocking issue(s)."
    )
    return {
        "verdict": verdict,
        "score": score,
        "risk": risk,
        "issues": issues,
        "summary": summary,
    }


def write_review_artifact(path: Path, review: dict, policies: dict | None = None) -> Path:
    workspace_dir = path.parent
    review_path = workspace_dir / "review.md"
    SafeArtifactWriter(Path.cwd(), policies).write_text(
        review_path,
        "# Review\n\n"
        "```json\n"
        f"{json.dumps(review, indent=2)}\n"
        "```\n",
        origin="reviewer",
    )
    return review_path


def verify_output(path: Path, policies: dict) -> dict:
    """The anti-fabrication gate: did anything real actually get produced?"""
    exists = path.exists() and path.stat().st_size > 0
    syntax_ok = False
    if exists:
        try:
            ast.parse(path.read_text(encoding="utf-8"))
            syntax_ok = True
        except SyntaxError:
            syntax_ok = False

    facts = {
        "output_empty": not exists,
        "syntax_invalid": exists and not syntax_ok,
        "file_not_written": not exists,
    }
    decision = evaluate("verify_output", facts, policies)
    return {"passed": not decision["escalate"], "decision": decision, "facts": facts}


def generate_commit_message(brief: dict, policies: dict, mock: bool) -> str:
    prompt = f"Write a single-line git commit message (conventional commits style) for this change:\n{json.dumps(brief)}"
    mock_msg = f"feat: {brief.get('title', 'add feature')}"
    return call_model("route_model_by_task", "commit_message", prompt, policies,
                       mock=mock, mock_response=mock_msg).strip()


def append_to_context(entry: str) -> None:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
    line = f"\n- [{ts}] {entry}"
    writer = SafeArtifactWriter(Path.cwd())
    if CONTEXT_FILE.exists():
        writer.append_text(CONTEXT_FILE, line, origin="orchestrator", allow_protected=True)
    else:
        writer.write_text(CONTEXT_FILE, f"# PROJECT_CONTEXT.md\n{line}", origin="orchestrator", allow_protected=True)

def _create_work_order_from_brief(wm: WorkOrderManager, brief: dict) -> WorkOrder:
    ac_objects = [
        AcceptanceCriterion(id=f"AC-{idx:03d}", description=desc, mandatory=True)
        for idx, desc in enumerate(brief["acceptance_criteria"], start=1)
    ]
    return wm.create(
        title=brief.get("title", "Generated Feature"),
        objective=brief.get("title", "Generated Feature"),
        department=Department.ARCHITECT,
        current_owner=Department.ARCHITECT.value,
        acceptance_criteria=ac_objects
    )

def run(feature_request: str, mock: bool) -> None:
    policies = load_policies()
    print(f"\n>> Feature request: {feature_request}")
    if mock:
        print(">> Mode: --mock (no API calls, free)\n")
    else:
        print(">> Mode: live (calling Groq)\n")

    print("[1/8] Architect: compiling scope...")
    scope_result = architect_scope_compile(feature_request, policies, mock)
    if scope_result["decision"]["escalate"]:
        print(f"  STOP [{scope_result['decision']['interrupt_level']}] — escalated to AK: {scope_result['decision']['reason']}")
        append_to_context(f"ESCALATED at scope_compile: {feature_request}")
        return
    brief = scope_result["brief"]
    
    # --- ETP Context & Artifact Workspace Initialization ---
    wm = WorkOrderManager()
    wo = _create_work_order_from_brief(wm, brief)

    workspace_dir = OUTPUT_DIR / "work_orders" / wo.id
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    etp_tracker = ETPTracker("1.0")

    def execute_handoff(dest_dept: Department, intent: TransferIntent, reason: str, reject_reason: str | None = None, deliverable_refs: list[str] | None = None):
        current_dept_str = getattr(wo.department, "value", wo.department)
        tx = etp_tracker.attempt_transfer(
            work_order_id=wo.id,
            current_department=current_dept_str,
            destination_department=dest_dept.value,
            intent=intent,
            reason=reason,
            reject_reason=reject_reason,
            deliverable_refs=deliverable_refs
        )
        record_etp_transaction(tx.to_dict())
        outcome_str = getattr(tx.outcome, "value", tx.outcome)
        if outcome_str == "ACCEPTED":
            wm.transfer_department(wo.id, dest_dept, owner=dest_dept.value, changed_by=tx.source_department, reason=reason)
        return tx
        
    execute_handoff(Department.REPOSITORY_INTELLIGENCE, TransferIntent.HANDOFF, "Architect to Repository Intelligence handoff")

    print("\n[2/8] Repository Intelligence: scanning...")
    scanner = RepositoryScanner()
    snapshot = scanner.scan(Path.cwd())
    profile = RepositoryIntelligence().build_profile(snapshot)

    execute_handoff(Department.FILE_SELECTION, TransferIntent.HANDOFF, "Repository Intelligence to File Selection handoff")

    print("\n[3/8] File Selection: computing relevance...")
    engine = FileSelectionEngine()
    selection = engine.select(wo, profile)

    fs_facts = {
        "zero_files_matched": len(selection.primary_files) == 0,
        "low_rule_coverage": selection.confidence < 0.5,
        "conflicting_rules": selection.escalation_reason == "conflicting_rules"
    }
    fs_decision = evaluate("file_selection", fs_facts, policies)
    
    if fs_decision["escalate"]:
        print(f"  STOP [{fs_decision['interrupt_level']}] — file_selection escalated: {fs_decision['reason']}")
        execute_handoff(Department.CONTEXT_BUILDER, TransferIntent.HANDOFF, "File Selection to Context Builder handoff", reject_reason=fs_decision['reason'])
        return

    execute_handoff(Department.CONTEXT_BUILDER, TransferIntent.HANDOFF, "File Selection to Context Builder handoff")

    print("\n[4/8] Context Builder: packaging artifacts...")
    builder = ContextBuilder()
    try:
        context = builder.build(wo, profile, selection)
    except Exception as e:
        print(f"  STOP [error] — Context Builder failed: {str(e)}")
        execute_handoff(Department.DEVELOPER, TransferIntent.HANDOFF, "Context Builder to Developer handoff", reject_reason=str(e))
        return

    context_path = workspace_dir / "context.json"
    writer = SafeArtifactWriter(Path.cwd(), policies)
    writer.write_text(context_path, json.dumps(asdict(context), indent=2), origin="context_builder", allow_protected=True)

    execute_handoff(Department.DEVELOPER, TransferIntent.HANDOFF, "Context Builder to Developer handoff", deliverable_refs=[str(context_path)])

    print("\n[5/8] Developer: generating code...")
    try:
        dev_result = developer_generate_code(context, policies, mock, wo.id)
    except ArtifactWriteError as exc:
        event = exc.event
        print(f"  STOP [approval] — filesystem_safety blocked artifact write: {event['reason']}")
        print(f"  Path: {event['attempted_path']}")
        append_to_context(f"BLOCKED at filesystem_safety: {feature_request} - {event['reason']}")
        execute_handoff(Department.REVIEWER, TransferIntent.REVIEW, "Developer to Reviewer handoff", reject_reason=event['reason'])
        return
    print(f"  Written to: {dev_result['path']}")

    execute_handoff(Department.REVIEWER, TransferIntent.REVIEW, "Developer to Reviewer handoff")

    print("\n[6/8] Reviewer: checking generated code...")
    review = review_generated_code(brief, dev_result)
    review_path = write_review_artifact(Path(dev_result["path"]), review, policies)
    record_review(feature_request, brief, dev_result["path"], str(review_path), review)
    review_decision = evaluate(
        "review_generated_code",
        {"review_failed": review["verdict"] == "FAIL"},
        policies,
    )
    print(f"  Verdict: {review['verdict']} score={review['score']} risk={review['risk']}")
    print(f"  Review artifact: {review_path}")
    if review_decision["escalate"]:
        print(f"  STOP [{review_decision['interrupt_level']}] — reviewer failed: {review['summary']}")
        for issue in review["issues"]:
            line = f":{issue['line']}" if "line" in issue else ""
            print(f"  - {issue['category']}{line}: {issue['message']}")
        append_to_context(f"FAILED at reviewer: {feature_request} - {review['summary']} -> {review_path}")
        execute_handoff(Department.VALIDATOR, TransferIntent.VALIDATE, "Reviewer to Verify handoff", reject_reason=review['summary'])
        return
    print("  Passed — no blocking review issues.")

    execute_handoff(Department.VALIDATOR, TransferIntent.VALIDATE, "Reviewer to Verify handoff")

    print("\n[7/8] Verify: checking the output is real...")
    verify_result = verify_output(Path(dev_result["path"]), policies)
    
    verify_path = workspace_dir / "verify.json"
    writer.write_text(verify_path, json.dumps(verify_result, default=str, indent=2), origin="validator", allow_protected=True)
    
    if not verify_result["passed"]:
        print(f"  STOP [{verify_result['decision']['interrupt_level']}] — escalated to AK: {verify_result['decision']['reason']}")
        print(f"  Facts: {verify_result['facts']}")
        append_to_context(f"ESCALATED at verify_output: {feature_request} — {verify_result['facts']}")
        execute_handoff(Department.HISTORIAN, TransferIntent.COMPLETE, "Verify to Commit handoff", reject_reason=verify_result['decision']['reason'])
        return
    print("  Passed — syntax valid, file non-empty.")

    execute_handoff(Department.HISTORIAN, TransferIntent.COMPLETE, "Verify to Commit handoff")

    print("\n[8/8] Commit message + log...")
    commit_msg = generate_commit_message(brief, policies, mock)
    print(f"  {commit_msg}")
    append_to_context(f"SHIPPED: {commit_msg} -> {dev_result['path']}")

    print(f"\nDone. AK gets: \"Ready for review: {dev_result['path']}\"")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AK Labs OS — minimal working orchestrator")
    parser.add_argument("feature", help="Feature request, e.g. 'Build a function that validates an email'")
    parser.add_argument("--mock", action="store_true", help="Run without hitting any API — free, offline")
    args = parser.parse_args()
    run(args.feature, mock=args.mock)