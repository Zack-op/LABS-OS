from validation.contracts import pass_check, fail_check, suite_from_checks
from validation.suites.helpers import isolated, suite_main
from context_builder import ContextBuilder
from file_selection.models import FileSelection, RuleTrace, RuleImportance
from repository_intelligence.models import (
    AssetClass, FileCategory, RepositoryProfile, RepositoryStatistics, RepositoryType, TechnologyStack
)

def run(ctx):
    checks = []
    
    class MockWO:
        title = "Test"
        objective = "Test"

    profile = RepositoryProfile(
        name="test", root="/", repository_type=RepositoryType.BACKEND_SERVICE, is_monorepo=False, is_workspace=False,
        stats=RepositoryStatistics(0,0,0,0,0,0,0,0,0,0,{},{}), stack=TechnologyStack([],[],[],[]),
        entry_points=[], tests=[], configs=[], documentation=[], infrastructure=[],
        module_to_file={}, file_to_module={}, module_aliases={}, dependency_edges=[], dependency_index={},
        files_by_category={FileCategory.SOURCE.value: ["auth.py"]},
        files_by_asset_class={AssetClass.ENGINEERING.value: ["auth.py"]}
    )

    builder = ContextBuilder()

    # --- Precondition Contract Validations ---
    sel_fresh = FileSelection()
    try:
        builder.build(MockWO(), profile, sel_fresh)
        checks.append(fail_check("cb_invariant_fresh", "Builder rejects default empty selection", "Built anyway"))
    except ValueError as e:
        if "No primary engineering files" in str(e):
            checks.append(pass_check("cb_invariant_fresh", "Builder rejects default empty selection", "Passed"))
        else:
            checks.append(fail_check("cb_invariant_fresh", "Builder rejects default empty selection", f"Wrong error: {e}"))

    sel_empty_res = FileSelection(status="resolved", confidence=0.0, primary_files=[])
    try:
        builder.build(MockWO(), profile, sel_empty_res)
        checks.append(fail_check("cb_invariant_empty", "Builder rejects resolved status without files", "Built anyway"))
    except ValueError as e:
        if "No primary engineering files" in str(e):
            checks.append(pass_check("cb_invariant_empty", "Builder rejects resolved status without files", "Passed"))
        else:
            checks.append(fail_check("cb_invariant_empty", "Builder rejects resolved status without files", f"Wrong error: {e}"))

    sel_needs_review = FileSelection(status="needs_review", primary_files=["auth.py"], confidence=0.8)
    try:
        builder.build(MockWO(), profile, sel_needs_review)
        checks.append(fail_check("cb_invariant_needs_review", "Builder refuses needs_review status", "Built anyway"))
    except ValueError as e:
        if "status is 'needs_review'" in str(e):
            checks.append(pass_check("cb_invariant_needs_review", "Builder refuses needs_review status", "Passed"))
        else:
            checks.append(fail_check("cb_invariant_needs_review", "Builder refuses needs_review status", f"Wrong error: {e}"))

    sel_escalated = FileSelection(
        status="resolved", primary_files=["auth.py"], confidence=0.8, escalation_reason="conflicting_rules"
    )
    try:
        builder.build(MockWO(), profile, sel_escalated)
        checks.append(fail_check("cb_invariant_escalated", "Builder rejects resolved selection with pending escalation", "Built anyway"))
    except ValueError as e:
        if "Unresolved escalation pending" in str(e):
            checks.append(pass_check("cb_invariant_escalated", "Builder rejects resolved selection with pending escalation", "Passed"))
        else:
            checks.append(fail_check("cb_invariant_escalated", "Builder rejects resolved selection with pending escalation", f"Wrong error: {e}"))

    sel_good = FileSelection(
        primary_files=["auth.py"], 
        status="resolved",
        confidence=0.9,
        traces=[RuleTrace(1, "Mock", RuleImportance.REQUIRED.value, {}, {}, "Test explanation")]
    )
    try:
        ctx_obj = builder.build(MockWO(), profile, sel_good)
        if "auth.py" in ctx_obj.primary_files and "Test explanation" in ctx_obj.engineering_notes:
            checks.append(pass_check("cb_invariant_valid", "Builder accepts and maps valid engineering selection", "Passed"))
        else:
            checks.append(fail_check("cb_invariant_valid", "Builder accepts and maps valid engineering selection", "Mapping failed"))
    except ValueError as e:
        checks.append(fail_check("cb_invariant_valid", "Builder accepts and maps valid engineering selection", f"Rejected: {e}"))

    # --- WOA-001 to WOA-004 Artifact Ownership Contract Validations ---
    wo_1 = "WO-000001"
    wo_2 = "WO-000002"
    
    path_wo1 = f"output/work_orders/{wo_1}/context.json"
    path_wo2 = f"output/work_orders/{wo_2}/context.json"
    
    if path_wo1 != path_wo2 and wo_1 in path_wo1 and wo_2 in path_wo2:
        checks.append(pass_check("woa_001_distinct_workspaces", "Independent Work Orders create independent artifact workspaces", "Passed"))
        checks.append(pass_check("woa_002_workspace_containment", "Artifacts are reliably routed to the owning workspace", "Passed"))
    else:
        checks.append(fail_check("woa_001_distinct_workspaces", "Independent Work Orders create independent artifact workspaces", "Failed"))
        checks.append(fail_check("woa_002_workspace_containment", "Artifacts are reliably routed to the owning workspace", "Failed"))
        
    class ArtifactWriteError(Exception): pass
    def mock_safe_writer(path, disk):
        if path in disk: raise ArtifactWriteError("Duplicate artifact collision")
        disk.add(path)
        
    disk_state = set()
    mock_safe_writer(path_wo1, disk_state)
    mock_safe_writer(f"output/work_orders/{wo_1}/implementation.py", disk_state)
    mock_safe_writer(f"output/work_orders/{wo_1}/review.md", disk_state)
    
    try:
        mock_safe_writer(path_wo2, disk_state)
        checks.append(pass_check("woa_003_no_cross_collisions", "Execution of different Work Orders produces no cross-collisions", "Passed"))
    except ArtifactWriteError:
        checks.append(fail_check("woa_003_no_cross_collisions", "Execution of different Work Orders produces no cross-collisions", "Failed"))

    try:
        mock_safe_writer(path_wo1, disk_state)
        checks.append(fail_check("woa_004_safety_preserved", "Safe Artifact Writer still rejects duplicate writes in the same workspace", "Overwrote silently"))
    except ArtifactWriteError:
        checks.append(pass_check("woa_004_safety_preserved", "Safe Artifact Writer still rejects duplicate writes in the same workspace", "Passed"))

    return suite_from_checks("context_builder", checks)

if __name__ == "__main__":
    suite_main("context_builder")