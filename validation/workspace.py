from __future__ import annotations

import shutil
import tempfile
from pathlib import Path


class ValidationWorkspace:
    def __init__(self, repo_root: Path, requested: str | None = None):
        self.repo_root = repo_root.resolve()
        self.requested = requested
        self.path: Path | None = None
        self._created_temp = False

    def __enter__(self) -> Path:
        if self.requested:
            path = Path(self.requested).resolve()
            try:
                path.relative_to(self.repo_root)
            except ValueError:
                pass
            else:
                raise ValueError("Validation workspace must not be inside the repository")
            path.mkdir(parents=True, exist_ok=True)
            self.path = path
        else:
            self.path = Path(tempfile.mkdtemp(prefix="ak_labs_validation_")).resolve()
            self._created_temp = True
        return self.path

    def __exit__(self, exc_type, exc, tb) -> None:
        # Keep validation workspaces for evidence. They are outside the repo.
        return None


def prepare_reports_dir(repo_root: Path) -> Path:
    reports_dir = repo_root / "reports"
    (reports_dir / "history").mkdir(parents=True, exist_ok=True)
    return reports_dir

