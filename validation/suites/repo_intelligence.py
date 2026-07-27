from __future__ import annotations
from pathlib import Path

from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import isolated, suite_main
from repository_intelligence import RepositoryScanner, RepositoryIntelligence, RepositoryType

def _create_mock_repo(workspace: Path):
    """Generates a mock mixed-stack repository for deterministic testing."""
    (workspace / "backend").mkdir()
    (workspace / "frontend" / "app").mkdir(parents=True)
    (workspace / "node_modules").mkdir()
    (workspace / ".github" / "workflows").mkdir(parents=True)
    
    # Python Backend
    (workspace / "backend" / "main.py").write_text("from fastapi import FastAPI", encoding="utf-8")
    (workspace / "backend" / "requirements.txt").write_text("fastapi==0.100.0", encoding="utf-8")
    
    # Next.js Frontend
    (workspace / "frontend" / "package.json").write_text('{"dependencies": {"next": "13.0.0"}}', encoding="utf-8")
    (workspace / "frontend" / "app" / "page.tsx").write_text("export default function Page() {}", encoding="utf-8")
    
    # Ignored & CI_CD
    (workspace / "node_modules" / "junk.js").write_text("junk", encoding="utf-8")
    (workspace / ".github" / "workflows" / "ci.yml").write_text("name: CI", encoding="utf-8")
    
    # Binary
    (workspace / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

def run(ctx):
    checks = []
    
    with isolated(ctx):
        mock_root = ctx.workspace / "mock_repo"
        mock_root.mkdir(exist_ok=True)
        _create_mock_repo(mock_root)
        
        scanner = RepositoryScanner()
        snapshot = scanner.scan(mock_root)
        
        # 1. Scanner Validation
        file_paths = {f.relative_path.replace("\\", "/") for f in snapshot.files}
        
        if "node_modules/junk.js" not in file_paths and snapshot.snapshot_version == "1.0":
            checks.append(pass_check("scanner_basics", "Scanner handles ignores and schema versions", "Passed"))
        else:
            checks.append(fail_check("scanner_basics", "Scanner handles ignores and schema versions", "Failed"))

        # Verify Binary & New Categories
        bin_files = [f for f in snapshot.files if f.is_binary]
        ci_files = [f for f in snapshot.files if f.category.value == "CI_CD"]
        if len(bin_files) == 1 and bin_files[0].name == "image.png" and len(ci_files) == 1:
            checks.append(pass_check("scanner_binary_categories", "Scanner identifies binaries and CI/CD correctly", "Passed"))
        else:
            checks.append(fail_check("scanner_binary_categories", "Scanner identifies binaries and CI/CD correctly", f"Binaries: {len(bin_files)}, CI: {len(ci_files)}"))

        # 2. Intelligence Validation
        intelligence = RepositoryIntelligence()
        profile = intelligence.build_profile(snapshot)
        
        # Indexes Check
        if "frontend/app/page.tsx" in profile.files_by_extension.get(".tsx", []) and len(profile.files_by_category.get("DEPENDENCY", [])) == 2:
            checks.append(pass_check("intelligence_indexes", "Intelligence precomputes deterministic indexes", "Passed"))
        else:
            checks.append(fail_check("intelligence_indexes", "Intelligence precomputes deterministic indexes", "Failed"))

        # Multi-Indicator Framework & Type Check
        fw_names = {fw.name for fw in profile.stack.frameworks}
        if "Next.js" in fw_names and "FastAPI" in fw_names:
            checks.append(pass_check("intelligence_frameworks", "Intelligence leverages multi-indicator rules", str(fw_names)))
        else:
            checks.append(fail_check("intelligence_frameworks", "Intelligence leverages multi-indicator rules", str(fw_names)))

        if profile.repository_type == RepositoryType.MONOREPO.value:
            checks.append(pass_check("intelligence_repo_type", "Intelligence assigns deterministic RepositoryType", profile.repository_type))
        else:
            checks.append(fail_check("intelligence_repo_type", "Intelligence assigns deterministic RepositoryType", profile.repository_type))

    return suite_from_checks("repo_intelligence", checks)

if __name__ == "__main__":
    suite_main("repo_intelligence")