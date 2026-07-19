from __future__ import annotations

from work_orders.enums import WorkOrderStatus
from work_orders.exceptions import InvalidLifecycleTransitionError
from work_orders.models import StatusTransition, WorkOrder


ALLOWED_TRANSITIONS: dict[WorkOrderStatus, set[WorkOrderStatus]] = {
    WorkOrderStatus.DRAFT: {WorkOrderStatus.APPROVED},
    WorkOrderStatus.APPROVED: {WorkOrderStatus.IN_PROGRESS},
    WorkOrderStatus.IN_PROGRESS: {WorkOrderStatus.READY_FOR_REVIEW},
    WorkOrderStatus.READY_FOR_REVIEW: {
        WorkOrderStatus.REVIEW_FAILED,
        WorkOrderStatus.READY_FOR_VALIDATION,
    },
    WorkOrderStatus.REVIEW_FAILED: {WorkOrderStatus.IN_PROGRESS},
    WorkOrderStatus.READY_FOR_VALIDATION: {
        WorkOrderStatus.VALIDATION_FAILED,
        WorkOrderStatus.COMPLETED,
    },
    WorkOrderStatus.VALIDATION_FAILED: {WorkOrderStatus.IN_PROGRESS},
    WorkOrderStatus.COMPLETED: {WorkOrderStatus.ARCHIVED},
    WorkOrderStatus.ARCHIVED: set(),
}


def can_transition(from_status: WorkOrderStatus | str, to_status: WorkOrderStatus | str) -> bool:
    source = WorkOrderStatus(from_status)
    target = WorkOrderStatus(to_status)
    return target in ALLOWED_TRANSITIONS[source]


def transition_status(
    work_order: WorkOrder,
    to_status: WorkOrderStatus | str,
    *,
    changed_at: str,
    changed_by: str,
    reason: str = "",
) -> WorkOrder:
    source = WorkOrderStatus(work_order.status)
    target = WorkOrderStatus(to_status)
    if not can_transition(source, target):
        raise InvalidLifecycleTransitionError(source.value, target.value)
    work_order.status = target
    work_order.status_history.append(StatusTransition(source.value, target, changed_at, changed_by, reason))
    return work_order
