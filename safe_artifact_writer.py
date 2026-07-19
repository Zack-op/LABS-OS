from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Iterable

from policy_engine import evaluate


INVALID_FILENAME_CHARS = set('<>:"|?*')
RESERVED_FILENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}
PROTECTED_PREFIXES = (
    "validation/",
    "reporters/",
    "policies/",
    "historian/",
    "reports/",
)
PROTECTED_EXACT = {
    ".env",
    ".env.example",
    "ARCHITECTURE.md",
    "RELEASE_SUMMARY.md",
    "PROJECT_CONTEXT.md",
    "ak_labs_os.db",
    "capabilities.yaml",
    "culture.yaml",
    "historian.py",
    "llm_router.py",
    "orchestrator.py",
    "policies.yaml",
    "policy_engine.py",
    "requirements.txt",
    "safe_artifact_writer.py",
}


class ArtifactWriteError(RuntimeError):
    """Structured filesystem safety failure raised before disk mutation."""

    def __init__(self, event: dict):
        self.event = event
        super().__init__(event["reason"])


def slugify_artifact_title(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40]


class SafeArtifactWriter:
    def __init__(self, workspace: Path | str | None = None, policies: dict | None = None):
        self.workspace = Path(workspace or ".").resolve()
        self.policies = policies

    def artifact_path_for_title(self, title: str, extension: str = ".py", directory: str = "output") -> Path:
        self._validate_title(title)
        slug = slugify_artifact_title(title)
        if not slug:
            self._block("invalid_filename", title, "Title does not produce a usable artifact name", "developer")
        return Path(directory) / f"{slug}{extension}"

    def write_text(
        self,
        relative_path: Path | str,
        content: str,
        *,
        origin: str,
        overwrite: bool = False,
        allow_protected: bool = False,
        authorized_protected_paths: Iterable[str] | None = None,
    ) -> Path:
        target = self._approved_target(
            relative_path,
            origin,
            operation="write",
            overwrite=overwrite,
            allow_existing=overwrite,
            allow_protected=allow_protected,
            authorized_protected_paths=authorized_protected_paths,
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def append_text(
        self,
        relative_path: Path | str,
        content: str,
        *,
        origin: str,
        allow_protected: bool = False,
        authorized_protected_paths: Iterable[str] | None = None,
    ) -> Path:
        target = self._approved_target(
            relative_path,
            origin,
            operation="append",
            overwrite=False,
            allow_existing=True,
            allow_protected=allow_protected,
            authorized_protected_paths=authorized_protected_paths,
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(content)
        return target

    def rename(
        self,
        source: Path | str,
        destination: Path | str,
        *,
        origin: str,
        allow_protected: bool = False,
        authorized_protected_paths: Iterable[str] | None = None,
    ) -> Path:
        src = self._approved_target(
            source,
            origin,
            operation="rename_source",
            overwrite=False,
            allow_existing=True,
            allow_protected=allow_protected,
            authorized_protected_paths=authorized_protected_paths,
        )
        dst = self._approved_target(
            destination,
            origin,
            operation="rename_destination",
            overwrite=False,
            allow_existing=False,
            allow_protected=allow_protected,
            authorized_protected_paths=authorized_protected_paths,
        )
        dst.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dst)
        return dst

    def delete(
        self,
        relative_path: Path | str,
        *,
        origin: str,
        allow_protected: bool = False,
        authorized_protected_paths: Iterable[str] | None = None,
    ) -> None:
        target = self._approved_target(
            relative_path,
            origin,
            operation="delete",
            overwrite=False,
            allow_existing=True,
            allow_protected=allow_protected,
            authorized_protected_paths=authorized_protected_paths,
        )
        target.unlink()

    def _validate_title(self, title: str) -> None:
        if not isinstance(title, str) or not title.strip():
            self._block("invalid_filename", str(title), "Artifact title must be a non-empty string", "developer")
        raw = title.strip()
        if self._is_absolute(raw):
            self._block("absolute_path", raw, "Absolute artifact paths are not allowed", "developer")
        if ".." in self._path_parts(raw):
            self._block("path_traversal", raw, "Path traversal is not allowed", "developer")
        if "/" in raw or "\\" in raw:
            self._block("recursive_path", raw, "Artifact titles may not contain path separators", "developer")
        self._validate_path_part(raw, raw, "developer")

    def _approved_target(
        self,
        relative_path: Path | str,
        origin: str,
        *,
        operation: str,
        overwrite: bool,
        allow_existing: bool,
        allow_protected: bool,
        authorized_protected_paths: Iterable[str] | None,
    ) -> Path:
        raw = str(relative_path)
        if not raw.strip():
            self._block("invalid_filename", raw, "Artifact path must not be empty", origin, operation)
        if self._is_absolute(raw):
            self._block("absolute_path", raw, "Absolute artifact paths are not allowed", origin, operation)

        parts = self._path_parts(raw)
        if any(part == ".." for part in parts):
            self._block("path_traversal", raw, "Path traversal is not allowed", origin, operation)
        if not parts:
            self._block("invalid_filename", raw, "Artifact path has no usable filename", origin, operation)
        for part in parts:
            self._validate_path_part(part, raw, origin, operation)

        normalized = "/".join(parts)
        if self._is_protected(normalized) and not self._is_authorized(
            normalized,
            allow_protected,
            authorized_protected_paths,
        ):
            self._block("protected_file", raw, "Protected project files require explicit authorization", origin, operation)

        target = (self.workspace / Path(*parts)).resolve(strict=False)
        self._ensure_inside_workspace(target, raw, origin, operation)
        if target.exists() and not allow_existing:
            reason = "Duplicate artifact collision; existing artifacts are never overwritten silently"
            self._block("duplicate_collision", raw, reason, origin, operation, normalized_path=target)
        if overwrite and target.exists() and self._is_protected(normalized) and not allow_protected:
            self._block("protected_file", raw, "Protected project files may not be overwritten", origin, operation)
        return target

    def _ensure_inside_workspace(self, target: Path, raw: str, origin: str, operation: str) -> None:
        try:
            target.relative_to(self.workspace)
        except ValueError:
            self._block("workspace_escape", raw, "Artifact path resolves outside the approved workspace", origin, operation, normalized_path=target)

        parent = target.parent
        if parent.exists():
            resolved_parent = parent.resolve()
            try:
                resolved_parent.relative_to(self.workspace)
            except ValueError:
                self._block("symlink_escape", raw, "Artifact parent resolves outside the approved workspace", origin, operation, normalized_path=resolved_parent)
        if target.exists():
            resolved_target = target.resolve()
            try:
                resolved_target.relative_to(self.workspace)
            except ValueError:
                self._block("symlink_escape", raw, "Artifact target resolves outside the approved workspace", origin, operation, normalized_path=resolved_target)

    def _validate_path_part(self, part: str, raw: str, origin: str, operation: str = "write") -> None:
        if part in {"", ".", ".."}:
            self._block("invalid_filename", raw, f"Invalid path segment: {part!r}", origin, operation)
        if any(ord(ch) < 32 for ch in part) or any(ch in INVALID_FILENAME_CHARS for ch in part):
            self._block("invalid_filename", raw, "Filename contains characters forbidden by AK Labs OS", origin, operation)
        reserved_base = part.split(".")[0].upper()
        if reserved_base in RESERVED_FILENAMES:
            self._block("reserved_filename", raw, f"Reserved filename is not allowed: {reserved_base}", origin, operation)

    def _block(
        self,
        reason_code: str,
        attempted_path: str,
        reason: str,
        origin: str,
        operation: str = "write",
        normalized_path: Path | None = None,
    ) -> None:
        event = {
            "policy": "filesystem_safety",
            "severity": "HIGH",
            "reason": reason,
            "reason_code": reason_code,
            "path": attempted_path,
            "attempted_path": attempted_path,
            "normalized_analysis": str(normalized_path) if normalized_path else None,
            "action": "BLOCKED",
            "operation": operation,
            "originating_department": origin,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._record_block(event)
        raise ArtifactWriteError(event)

    def _record_block(self, event: dict) -> None:
        facts = {
            "filesystem_blocked": True,
            "reason_code": event["reason_code"],
            "attempted_path": event["attempted_path"],
            "operation": event["operation"],
            "originating_department": event["originating_department"],
        }
        try:
            event["policy_decision"] = evaluate("filesystem_safety", facts, self.policies)
        except Exception as exc:
            event["policy_error"] = repr(exc)
        try:
            from historian import record_filesystem_event

            record_filesystem_event(event)
        except Exception as exc:
            event["historian_error"] = repr(exc)

    @staticmethod
    def _is_absolute(raw: str) -> bool:
        return Path(raw).is_absolute() or PureWindowsPath(raw).is_absolute()

    @staticmethod
    def _path_parts(raw: str) -> list[str]:
        return [part for part in re.split(r"[\\/]+", raw.strip()) if part]

    @staticmethod
    def _is_authorized(
        normalized: str,
        allow_protected: bool,
        authorized_protected_paths: Iterable[str] | None,
    ) -> bool:
        if allow_protected:
            return True
        authorized = {path.replace("\\", "/").strip("/") for path in authorized_protected_paths or []}
        return normalized in authorized

    @staticmethod
    def _is_protected(normalized: str) -> bool:
        path = normalized.strip("/")
        lower = path.lower()
        if path in PROTECTED_EXACT or lower in {item.lower() for item in PROTECTED_EXACT}:
            return True
        return any(lower.startswith(prefix.lower()) for prefix in PROTECTED_PREFIXES)


def event_to_json(event: dict) -> str:
    return json.dumps(event, sort_keys=True, ensure_ascii=True)
