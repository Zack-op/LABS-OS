from __future__ import annotations
from collections import defaultdict
from pathlib import Path
from validation.contracts import fail_check, pass_check, suite_from_checks
from validation.suites.helpers import isolated, suite_main
from repository_intelligence import (
    AssetClass, FileCategory, RelationshipType, RepositoryType,
    RepositoryScanner, RepositoryIntelligence
)

def _create_mock_repo(workspace: Path):
    (workspace / "backend").mkdir()
    (workspace / "frontend" / "app").mkdir(parents=True)
    (workspace / "node_modules").mkdir()
    (workspace / ".github" / "workflows").mkdir(parents=True)
    (workspace / "output").mkdir(parents=True)
    
    (workspace / "backend" / "main.py").write_text("from fastapi import FastAPI\nimport backend.utils.helper", encoding="utf-8")
    (workspace / "backend" / "utils").mkdir()
    (workspace / "backend" / "utils" / "helper.py").write_text("def assist(): pass", encoding="utf-8")
    (workspace / "backend" / "requirements.txt").write_text("fastapi==0.100.0", encoding="utf-8")
    
    (workspace / "frontend" / "package.json").write_text('{"dependencies": {"next": "13.0.0"}}', encoding="utf-8")
    (workspace / "frontend" / "app" / "page.tsx").write_text("export default function Page() {}", encoding="utf-8")
    
    (workspace / "node_modules" / "junk.js").write_text("junk", encoding="utf-8")
    (workspace / "output" / "build.log").write_text("log data", encoding="utf-8")
    (workspace / ".github" / "workflows" / "ci.yml").write_text("name: CI", encoding="utf-8")

def run(ctx):
    checks = []
    
    with isolated(ctx):
        mock_root = ctx.workspace / "mock_repo"
        mock_root.mkdir(exist_ok=True)
        _create_mock_repo(mock_root)
        
        scanner = RepositoryScanner()
        snapshot = scanner.scan(mock_root)
        intelligence = RepositoryIntelligence()
        profile = intelligence.build_profile(snapshot)
        
        # --- RI-R003 Graph Integrity & Canonical Identity Verifications ---
        
        invalid_sources = [e.source for e in profile.dependency_edges if e.source not in profile.module_to_file]
        invalid_targets = [e.target for e in profile.dependency_edges if e.target not in profile.module_to_file]
        
        if not invalid_sources and not invalid_targets:
            checks.append(pass_check("intelligence_canonical_graph_integrity", "DependencyEdge strictly uses canonical modules", "Passed"))
        else:
            checks.append(fail_check("intelligence_canonical_graph_integrity", "DependencyEdge strictly uses canonical modules", f"Invalid Sources = {len(invalid_sources)}, Invalid Targets = {len(invalid_targets)}"))
            
        round_trip_failures = 0
        for f, mod in profile.file_to_module.items():
            if profile.module_to_file.get(mod) != f:
                round_trip_failures += 1
                
        if round_trip_failures == 0:
            checks.append(pass_check("intelligence_canonical_roundtrip", "Canonical round-trip preserves 1:1 identity", "Passed"))
        else:
            checks.append(fail_check("intelligence_canonical_roundtrip", "Canonical round-trip preserves 1:1 identity", f"Failures: {round_trip_failures}"))

        expected_index = defaultdict(list)
        for e in profile.dependency_edges:
            s_file = profile.module_to_file.get(e.source)
            t_file = profile.module_to_file.get(e.target)
            if s_file and t_file and t_file not in expected_index[s_file]:
                expected_index[s_file].append(t_file)
                
        consistency_failures = 0
        for src_file, targets in profile.dependency_index.items():
            if src_file not in expected_index:
                consistency_failures += 1
            for t in targets:
                if t not in expected_index[src_file]:
                    consistency_failures += 1
                    
        if consistency_failures == 0:
            checks.append(pass_check("intelligence_runtime_consistency", "Runtime index is strictly derivable from canonical graph", "Passed"))
        else:
            checks.append(fail_check("intelligence_runtime_consistency", "Runtime index is strictly derivable from canonical graph", f"Orphaned edges: {consistency_failures}"))

        self_edges = [e for e in profile.dependency_edges if e.source == e.target]
        duplicates = len(profile.dependency_edges) - len(set((e.source, e.target, e.relationship) for e in profile.dependency_edges))
        
        if not self_edges and duplicates == 0:
            checks.append(pass_check("intelligence_graph_deduplication", "No self edges and no duplicate canonical edges", "Passed"))
        else:
            checks.append(fail_check("intelligence_graph_deduplication", "No self edges and no duplicate canonical edges", f"Self: {len(self_edges)}, Dups: {duplicates}"))
            
        # --- End RI-R003 Check Block ---

        alias_resolves_base = profile.module_aliases.get("helper") == "backend.utils.helper"
        alias_resolves_full = profile.module_aliases.get("helper.py") == "backend.utils.helper"
        
        if alias_resolves_base and alias_resolves_full:
            checks.append(pass_check("intelligence_alias_resolution", "Aliases deterministically map to canonical modules", "Passed"))
        else:
            checks.append(fail_check("intelligence_alias_resolution", "Aliases deterministically map to canonical modules", "Failed"))

    return suite_from_checks("repo_intelligence", checks)

if __name__ == "__main__":
    suite_main("repo_intelligence")