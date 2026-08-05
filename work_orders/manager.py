from datetime import datetime, timezone
from work_orders.ids import WorkOrderIdGenerator
from work_orders.models import WorkOrder
from work_orders.enums import Department

class WorkOrderNotFoundError(Exception):
    pass

class WorkOrderManager:
    """
    Manages the lifecycle, lookup, and department transfers of Work Orders.
    Guarantees canonical indexing against the immutable Work Order ID.
    """
    def __init__(self, generator: WorkOrderIdGenerator | None = None):
        self._orders: dict[str, WorkOrder] = {}
        self._generator = generator or WorkOrderIdGenerator()

    def create(self, title: str, objective: str, department: Department, current_owner: str, acceptance_criteria: list = None) -> WorkOrder:
        wo_id = self._generator.generate()
        
        # Synchronized with the updated WorkOrder model contract
        wo = WorkOrder(
            id=wo_id,
            title=title,
            description=objective,          # Fallback to objective for description
            objective=objective,
            department=department,
            priority="Medium",              # Sensible system default
            status="Draft",                 # Sensible system default
            current_owner=current_owner,
            created_at=datetime.now(timezone.utc).isoformat(),
            created_by="System",            # Standard orchestrator originator
            acceptance_criteria=acceptance_criteria or []
        )
        
        self._orders[wo.id] = wo
        return wo

    def get(self, wo_id: str) -> WorkOrder:
        if wo_id not in self._orders:
            raise WorkOrderNotFoundError(f"work order not found: {wo_id}")
        return self._orders[wo_id]

    def transfer_department(self, wo_id: str, new_department: Department, owner: str, changed_by: str, reason: str) -> None:
        wo = self.get(wo_id)
        wo.department = new_department
        wo.current_owner = owner