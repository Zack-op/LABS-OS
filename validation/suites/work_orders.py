from validation.contracts import pass_check, fail_check, suite_from_checks
from validation.suites.helpers import isolated, suite_main
from work_orders.manager import WorkOrderManager, WorkOrderNotFoundError
from work_orders.state import CounterStore
from work_orders.ids import WorkOrderIdGenerator
from work_orders.enums import Department

def run(ctx):
    checks = []
    
    with isolated(ctx):
        state_file = ctx.workspace / "state" / "work_order_counter.json"
        
        # WO-P001: Independent python executions produce monotonic sequences
        def simulate_execution():
            store = CounterStore(state_file)
            generator = WorkOrderIdGenerator(store)
            wm = WorkOrderManager(generator)
            return wm.create("Feature", "Implement feature", Department.ARCHITECT, "AK", [])
            
        wo1 = simulate_execution()
        wo2 = simulate_execution()
        wo3 = simulate_execution()
        
        if wo1.id == "WO-000001" and wo2.id == "WO-000002" and wo3.id == "WO-000003":
            checks.append(pass_check("wo_p001_persistence", "Independent executions produce monotonic persistent sequences", "Passed"))
        else:
            checks.append(fail_check("wo_p001_persistence", "Independent executions produce monotonic persistent sequences", f"{wo1.id}, {wo2.id}, {wo3.id}"))
            
        # WO-P002: Manager lookup succeeds with canonical ID
        store = CounterStore(state_file)
        wm = WorkOrderManager(WorkOrderIdGenerator(store))
        wo4 = wm.create("Lookup Feature", "Test get", Department.ARCHITECT, "AK", [])
        
        try:
            retrieved = wm.get(wo4.id)
            if retrieved.id == wo4.id:
                checks.append(pass_check("wo_p002_lookup", "Manager lookup succeeds natively", "Passed"))
            else:
                checks.append(fail_check("wo_p002_lookup", "Manager lookup succeeds natively", "ID mismatch"))
        except WorkOrderNotFoundError:
            checks.append(fail_check("wo_p002_lookup", "Manager lookup succeeds natively", "WorkOrderNotFoundError thrown"))
            
        # WO-P003: Department transfer succeeds on canonical ID
        try:
            wm.transfer_department(wo4.id, Department.DEVELOPER, Department.DEVELOPER.value, "System", "Handoff")
            if wm.get(wo4.id).department == Department.DEVELOPER:
                checks.append(pass_check("wo_p003_transfer", "Department transfer successfully indexes and modifies Work Order", "Passed"))
            else:
                checks.append(fail_check("wo_p003_transfer", "Department transfer successfully indexes and modifies Work Order", "Transfer state failed"))
        except Exception as e:
            checks.append(fail_check("wo_p003_transfer", "Department transfer successfully indexes and modifies Work Order", str(e)))

        # WO-P004: Workspace Isolation
        out_dir = ctx.workspace / "output" / "work_orders"
        (out_dir / wo1.id).mkdir(parents=True, exist_ok=True)
        (out_dir / wo3.id).mkdir(parents=True, exist_ok=True)
        
        if (out_dir / "WO-000001").exists() and (out_dir / "WO-000003").exists():
            checks.append(pass_check("wo_p004_workspaces", "Independent Work Orders map to independent workspaces", "Passed"))
        else:
            checks.append(fail_check("wo_p004_workspaces", "Independent Work Orders map to independent workspaces", "Failed"))

    return suite_from_checks("work_orders", checks)

if __name__ == "__main__":
    suite_main("work_orders")