from __future__ import annotations
import os
import mimetypes
from pathlib import Path

from repository_intelligence.models import (
    FileCategory,
    RepositoryDirectory,
    RepositoryFile,
    RepositorySnapshot,
)

DEFAULT_IGNORED_DIRS = {
    ".git", ".github/cache", ".venv", "venv", "node_modules", "dist", "build", 
    "coverage", ".pytest_cache", "__pycache__", ".next", ".idea", 
    ".vscode", ".cache", "tmp", "temp"
}

LANGUAGE_EXTENSIONS = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", 
    ".jsx": "React", ".tsx": "React/TypeScript", ".html": "HTML", 
    ".css": "CSS", ".json": "JSON", ".md": "Markdown", ".yaml": "YAML", 
    ".yml": "YAML", ".sh": "Shell", ".sql": "SQL", ".java": "Java", 
    ".go": "Go", ".rs": "Rust", ".toml": "TOML", ".cs": "C#"
}

KNOWN_BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".pyc", ".whl", 
    ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".dylib", ".bin", ".sqlite"
}

class RepositoryScanner:
    """Deterministically walks a repository and produces a structured snapshot."""

    def __init__(self, ignored_dirs: set[str] | None = None):
        self.ignored_dirs = ignored_dirs or DEFAULT_IGNORED_DIRS

    def scan(self, root_path: str | Path) -> RepositorySnapshot:
        root = Path(root_path).resolve()
        files: list[RepositoryFile] = []
        directories: list[RepositoryDirectory] = []
        ignored_count = 0

        for dirpath_str, dirnames, filenames in os.walk(str(root)):
            current_dir = Path(dirpath_str)
            
            original_dir_count = len(dirnames)
            # Handle exact matches and nested exclusions (e.g., .github/cache vs .github)
            dirnames[:] = [d for d in dirnames if not self._is_ignored_dir(current_dir / d, root)]
            ignored_count += (original_dir_count - len(dirnames))

            rel_dir = current_dir.relative_to(root)
            depth = len(rel_dir.parts)

            if current_dir != root:
                directories.append(RepositoryDirectory(
                    relative_path=str(rel_dir).replace("\\", "/"),
                    absolute_path=str(current_dir),
                    name=current_dir.name,
                    depth=depth,
                    is_hidden=current_dir.name.startswith("."),
                    parent_dir=str(rel_dir.parent).replace("\\", "/")
                ))

            for filename in filenames:
                file_path = current_dir / filename
                rel_file = file_path.relative_to(root)
                ext = file_path.suffix.lower()

                is_hidden = filename.startswith(".")
                size_bytes = file_path.stat().st_size if file_path.exists() else 0
                is_bin = self._is_binary(file_path, ext, size_bytes)
                language = LANGUAGE_EXTENSIONS.get(ext)
                category = self._categorize_file(filename, ext, str(rel_dir))

                files.append(RepositoryFile(
                    relative_path=str(rel_file).replace("\\", "/"),
                    absolute_path=str(file_path),
                    name=filename,
                    depth=depth + 1,
                    is_hidden=is_hidden,
                    parent_dir=str(rel_dir).replace("\\", "/"),
                    extension=ext,
                    size_bytes=size_bytes,
                    is_binary=is_bin,
                    language=language,
                    category=category
                ))

        return RepositorySnapshot(
            root_path=str(root),
            files=files,
            directories=directories,
            ignored_count=ignored_count,
            snapshot_version="1.0"
        )

    def _is_ignored_dir(self, dir_path: Path, root: Path) -> bool:
        rel = str(dir_path.relative_to(root)).replace("\\", "/")
        if dir_path.name in self.ignored_dirs:
            return True
        return rel in self.ignored_dirs

    def _is_binary(self, file_path: Path, ext: str, size: int) -> bool:
        if ext in KNOWN_BINARY_EXTENSIONS:
            return True
        if size == 0:
            return False
            
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if mime_type.startswith("text/") or mime_type in {"application/json", "application/javascript", "application/xml"}:
                return False
            if mime_type.startswith("image/") or mime_type.startswith("video/") or mime_type.startswith("audio/"):
                return True

        # Deterministic lightweight byte inspection (read first 1024 bytes)
        try:
            with file_path.open("rb") as f:
                chunk = f.read(1024)
                if b'\x00' in chunk:
                    return True
        except Exception:
            pass
            
        return False

    def _categorize_file(self, filename: str, ext: str, rel_dir: str) -> FileCategory:
        name_lower = filename.lower()
        path_lower = f"{rel_dir}/{filename}".replace("\\", "/").lower()

        if "test" in path_lower or "spec" in name_lower:
            return FileCategory.TEST
        if name_lower in {"package.json", "requirements.txt", "pyproject.toml", "cargo.toml", "go.mod", "pom.xml", "build.gradle", "poetry.lock", "package-lock.json"}:
            return FileCategory.DEPENDENCY
        if name_lower in {"dockerfile", "docker-compose.yml", "makefile"} or ext in {".tf", ".hcl"}:
            return FileCategory.INFRA
        if ".github/workflows" in path_lower or name_lower in {".gitlab-ci.yml", "jenkinsfile"}:
            return FileCategory.CI_CD
        if "migration" in path_lower or "alembic" in path_lower or name_lower.startswith("v1__"):
            return FileCategory.MIGRATION
        if ext in {".sql", ".sqlite"} or "schema" in name_lower:
            return FileCategory.DATABASE
        if ext in {".json", ".yaml", ".yml", ".toml", ".ini", ".env"} or "config" in name_lower:
            return FileCategory.CONFIG
        if ext in {".md", ".txt", ".rst"}:
            return FileCategory.DOC
        if ext in {".sh", ".bat", ".ps1"}:
            return FileCategory.SCRIPT
        if ext in KNOWN_BINARY_EXTENSIONS or ext in {".svg", ".woff", ".woff2"}:
            return FileCategory.ASSET
        if ext in LANGUAGE_EXTENSIONS and ext not in {".md", ".json", ".yaml", ".yml", ".toml"}:
            return FileCategory.SOURCE
            
        return FileCategory.UNKNOWN