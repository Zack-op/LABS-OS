import re
from typing import Optional
from work_orders.state import CounterStore

def validate_work_order_id(wo_id: str) -> bool:
    """
    Validates that a string matches the canonical Work Order ID format.
    Expected format: WO-XXXXXX (e.g., WO-000001)
    """
    if not isinstance(wo_id, str):
        return False
    return bool(re.fullmatch(r"^WO-\d{6}$", wo_id))

def parse_work_order_number(wo_id: str) -> int:
    """
    Extracts the sequence number from a canonical Work Order ID.
    Raises ValueError if the ID format is invalid.
    """
    if not validate_work_order_id(wo_id):
        raise ValueError(f"Invalid Work Order ID format: {wo_id}")
    return int(wo_id.split("-")[1])

class WorkOrderIdGenerator:
    """
    Domain logic for generating deterministic, strictly monotonic 
    Work Order IDs across independent Python executions.
    """
    def __init__(self, store: Optional[CounterStore] = None):
        self.store = store or CounterStore()

    def generate(self) -> str:
        seq = self.store.load()
        self.store.save(seq + 1)
        return f"WO-{seq:06d}"