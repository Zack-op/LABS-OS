from __future__ import annotations


class WorkOrderError(Exception):
    """Base exception for Work Order domain failures."""


class WorkOrderValidationError(WorkOrderError):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class DuplicateWorkOrderIdError(WorkOrderValidationError):
    def __init__(self, work_order_id: str):
        self.work_order_id = work_order_id
        super().__init__([f"duplicate work order id: {work_order_id}"])


class InvalidLifecycleTransitionError(WorkOrderError):
    def __init__(self, from_status: str, to_status: str):
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(f"invalid lifecycle transition: {from_status} -> {to_status}")


class WorkOrderNotFoundError(WorkOrderError):
    def __init__(self, work_order_id: str):
        self.work_order_id = work_order_id
        super().__init__(f"work order not found: {work_order_id}")
