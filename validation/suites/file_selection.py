import hashlib
from pathlib import Path
from validation.contracts import pass_check, fail_check, suite_from_checks
from validation.suites.helpers import isolated, suite_main
from file_selection import FileSelectionEngine
from repository_intelligence.models import (
    AssetClass, DependencyEdge, FileCategory, FrameworkSummary, RelationshipType, 
    RepositoryProfile, RepositoryStatistics, RepositoryType, TechnologyStack
)

def _create_large_physical_mock_repo(workspace: Path):
    dirs = [
        "backend/api", "backend/services", "backend/models", 
        "backend/repositories", "backend/config", "backend/utils", 
        "backend/tests", "docs", "output"
    ]
    for d in dirs:
        (workspace / d).mkdir(parents=True, exist_ok=True)
        
    files = {
        "backend/main.py": "from fastapi import FastAPI\nimport backend.api.routes\nimport backend.config.settings",
        "backend/api/routes.py": "import backend.services.auth\nimport backend.models.user\ndef get_health(): pass",
        "backend/services/auth.py": "import backend.repositories.user_repo\nimport backend.models.user\nimport backend.config.settings\nimport backend.utils.helpers",
        "backend/models/user.py": "class User: pass",
        "backend/repositories/user_repo.py": "import backend.models.user\nimport backend.config.settings",
        "backend/config/settings.py": "DATABASE_URL = ''",
        "backend/utils/helpers.py": "def hash_pw(): pass",
        "backend/tests/test_auth.py": "import backend.services.auth\ndef test_auth(): pass",
        "docs/api.md": "# API Documentation",
        "output/coverage.xml": "<coverage></coverage>"
    }
    for path, content in files.items():
        (workspace / path).write_text(content, encoding="utf-8")

def run(ctx):
    checks = []
    engine = FileSelectionEngine()
    
    with isolated(ctx):
        # ---------------------------------------------------------
        # PHASE 1: UNIT VALIDATION (Synthetic Profile)
        # ---------------------------------------------------------
        profile = RepositoryProfile(
            name="mock_project", root="/mock", repository_type=RepositoryType.BACKEND_SERVICE, 
            is_monorepo=False, is_workspace=False,
            stats=RepositoryStatistics(0,0,0,0,0,0,0,0,0,0,{},{}), 
            stack=TechnologyStack(languages=[], frameworks=[FrameworkSummary("FastAPI", ["fastapi"])], package_managers=[], build_systems=[]),
            entry_points=[], tests=[], configs=[], documentation=["docs/architecture.md"], infrastructure=[],
            module_to_file={
                "backend.models.user": "backend/models/user.py",
                "backend.api.routes": "backend/api/routes.py"
            },
            file_to_module={
                "backend/models/user.py": "backend.models.user", 
                "backend/api/routes.py": "backend.api.routes"
            },
            dependency_edges=[
                DependencyEdge("backend/api/routes.py", "backend/models/user.py", RelationshipType.IMPORT)
            ],
            dependency_index={"backend/api/routes.py": ["backend/models/user.py"]},
            centrality_metrics={"backend/api/routes.py": 0.5, "backend/models/user.py": 0.2},
            files_by_category={
                FileCategory.DATABASE.value: ["backend/models/schema.sql"], 
                FileCategory.SOURCE.value: ["backend/api/routes.py", "backend/models/user.py"],
                FileCategory.DOC.value: ["docs/architecture.md"]
            },
            files_by_asset_class={
                AssetClass.ENGINEERING.value: ["backend/models/schema.sql", "backend/api/routes.py", "backend/models/user.py", "docs/architecture.md"],
                AssetClass.GENERATED.value: ["output/logs.txt"],
                AssetClass.TEMP.value: ["cache/cache.bin"]
            }
        )
        
        class ValidTaskWO:
            title = "Implement user endpoint"
            objective = "Add routes"
            constraints = []
            acceptance_criteria = []
            deliverables = [{"description": "API routes"}]

        sel_1 = engine.select(ValidTaskWO(), profile)
        if sel_1.status == "resolved" and sel_1.confidence >= 0.7:
            checks.append(pass_check("unit_weighted_confidence", "Weighted evidence formula computes accurately", "Passed"))
        else:
            checks.append(fail_check("unit_weighted_confidence", "Weighted evidence formula computes accurately", str(sel_1.confidence)))

        class AmbiguousTaskWO:
            title = "Optimize fluctuator"
            objective = "Flux capacitor"
            constraints = []
            acceptance_criteria = []
            deliverables = []
            
        sel_2 = engine.select(AmbiguousTaskWO(), profile)
        if sel_2.status == "needs_review" and sel_2.escalation_reason == "zero_files_matched" and sel_2.confidence == 0.0:
            checks.append(pass_check("unit_missing_primary", "Missing primary evidence forces confidence to 0.0", "Passed"))
        else:
            checks.append(fail_check("unit_missing_primary", "Missing primary evidence forces confidence to 0.0", str(sel_2.confidence)))

        sel_3a = engine.select(ValidTaskWO(), profile)
        sel_3b = engine.select(ValidTaskWO(), profile)
        hash_a = hashlib.sha256(str(sel_3a.to_dict() if hasattr(sel_3a, "to_dict") else vars(sel_3a)).encode()).hexdigest()
        hash_b = hashlib.sha256(str(sel_3b.to_dict() if hasattr(sel_3b, "to_dict") else vars(sel_3b)).encode()).hexdigest()
        
        if hash_a == hash_b:
            checks.append(pass_check("unit_determinism", "Identical tasks yield matching SHA-256 state signatures", "Passed"))
        else:
            checks.append(fail_check("unit_determinism", "Identical tasks yield matching SHA-256 state signatures", "Hash mismatch"))

        # ---------------------------------------------------------
        # PHASE 2: INTEGRATION VALIDATION (Realistic Physical Mock)
        # ---------------------------------------------------------
        mock_root = ctx.workspace / "mock_integration"
        mock_root.mkdir()
        _create_large_physical_mock_repo(mock_root)
        
        from repository_intelligence.scanner import RepositoryScanner
        from repository_intelligence.intelligence import RepositoryIntelligence
        
        scanner = RepositoryScanner()
        snapshot = scanner.scan(mock_root)
        intel = RepositoryIntelligence()
        real_profile = intel.build_profile(snapshot)
        
        class RealValidTaskWO:
            title = "Implement user authentication logic"
            objective = "Build auth endpoints and verify users"
            constraints = []
            acceptance_criteria = []
            deliverables = [{"description": "Authentication service integration"}]
            
        real_sel = engine.select(RealValidTaskWO(), real_profile)
        
        if "backend/services/auth.py" in real_sel.primary_files or "backend/api/routes.py" in real_sel.primary_files:
            if "backend/config/settings.py" not in real_sel.primary_files:
                checks.append(pass_check("integration_category_aware_centrality", "Dependency-aware ranking succeeds while bounding infrastructure centrality", "Passed"))
            else:
                checks.append(fail_check("integration_category_aware_centrality", "Dependency-aware ranking succeeds while bounding infrastructure centrality", "Config file improperly dominated rankings"))
        else:
            checks.append(fail_check("integration_category_aware_centrality", "Dependency-aware ranking succeeds while bounding infrastructure centrality", str(real_sel.primary_files)))
            
        if "backend/tests/test_auth.py" in real_sel.supporting_files or "backend/repositories/user_repo.py" in real_sel.supporting_files:
            checks.append(pass_check("integration_dependency_expansion", "Valid task organically expands into testing and repository dependencies", "Passed"))
        else:
            checks.append(fail_check("integration_dependency_expansion", "Valid task organically expands into testing and repository dependencies", str(real_sel.supporting_files)))

        class RealGenTaskWO:
            title = "Analyze logs"
            objective = "Read output logs"
            constraints = []
            acceptance_criteria = []
            deliverables = []
            
        real_gen_sel = engine.select(RealGenTaskWO(), real_profile)
        if "output/coverage.xml" in real_gen_sel.primary_files:
            checks.append(pass_check("integration_generated_task", "Integration scan handles explicit generated artifacts", "Passed"))
        else:
            checks.append(fail_check("integration_generated_task", "Integration scan handles explicit generated artifacts", str(real_gen_sel.primary_files)))
            
        class RealDocTaskWO:
            title = "Update documentation"
            objective = "Document API changes"
            constraints = []
            acceptance_criteria = []
            deliverables = []
            
        real_doc_sel = engine.select(RealDocTaskWO(), real_profile)
        if "docs/api.md" in real_doc_sel.primary_files:
            checks.append(pass_check("integration_doc_task", "Integration resolves documentation natively", "Passed"))
        else:
            checks.append(fail_check("integration_doc_task", "Integration resolves documentation natively", str(real_doc_sel.primary_files)))

    return suite_from_checks("file_selection", checks)

if __name__ == "__main__":
    suite_main("file_selection")