from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from work_orders.enums import Complexity, Department, Priority, RiskLevel, WorkOrderStatus
from work_orders.exceptions import DuplicateWorkOrderIdError, WorkOrderNotFoundError
from work_orders.ids import WorkOrderIdGenerator
from work_orders.lifecycle import transition_status
from work_orders.models import (
    AcceptanceCriterion,
    Deliverable,
    DepartmentTransition,
    StatusTransition,
    WorkOrder,
    WorkOrderContract,
)
from work_orders.validator import validate_work_order


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class WorkOrderManager:
    def __init__(
        self,
        *,
        id_generator: WorkOrderIdGenerator | None = None,
        timestamp_provider: Callable[[], str] = utc_now,
    ):
        self.id_generator = id_generator or WorkOrderIdGenerator()
        self.timestamp_provider = timestamp_provider
        self._orders: dict[str, WorkOrder] = {}

    def create(
        self,
        *,
        title: str,
        objective: str,
        description: str = "",
        created_by: str = "Architect",
        current_owner: str = "Architect",
        department: Department = Department.ARCHITECT,
        priority: Priority = Priority.MEDIUM,
        risk_level: RiskLevel = RiskLevel.LOW,
        estimated_complexity: Complexity = Complexity.M,
        repository: str = "",
        constraints: list[str] | None = None,
        acceptance_criteria: list[AcceptanceCriterion] | None = None,
        deliverables: list[Deliverable] | None = None,
        dependencies: list[str] | None = None,
        affected_components: list[str] | None = None,
        artifact_targets: list[str] | None = None,
        review_requirements: list[str] | None = None,
        validation_requirements: list[str] | None = None,
        contract: WorkOrderContract | None = None,
        metadata: dict | None = None,
    ) -> WorkOrder:
        work_order_id = self.id_generator.next_id()
        created_at = self.timestamp_provider()
        order = WorkOrder(
            id=work_order_id,
            title=title,
            objective=objective,
            description=description,
            priority=priority,
            status=WorkOrderStatus.DRAFT,
            created_at=created_at,
            created_by=created_by,
            current_owner=current_owner,
            department=department,
            repository=repository,
            constraints=constraints or [],
            acceptance_criteria=acceptance_criteria or [],
            deliverables=deliverables or [],
            dependencies=dependencies or [],
            affected_components=affected_components or [],
            artifact_targets=artifact_targets or [],
            review_requirements=review_requirements or [],
            validation_requirements=validation_requirements or [],
            risk_level=risk_level,
            estimated_complexity=estimated_complexity,
            contract=contract or WorkOrderContract(),
            metadata=metadata or {},
            status_history=[
                StatusTransition(None, WorkOrderStatus.DRAFT, created_at, created_by, "created")
            ],
            department_history=[
                DepartmentTransition(None, department, current_owner, created_at, created_by, "created")
            ],
        )
        self.add(order)
        return order

    def add(self, work_order: WorkOrder) -> None:
        if work_order.id in self._orders:
            raise DuplicateWorkOrderIdError(work_order.id)
        validate_work_order(work_order)
        self._orders[work_order.id] = work_order
        self.id_generator.reserve(work_order.id)

    def get(self, work_order_id: str) -> WorkOrder:
        try:
            return self._orders[work_order_id]
        except KeyError as exc:
            raise WorkOrderNotFoundError(work_order_id) from exc

    def list(self) -> list[WorkOrder]:
        return [self._orders[key] for key in sorted(self._orders)]

    def transition(
        self,
        work_order_id: str,
        to_status: WorkOrderStatus,
        *,
        changed_by: str,
        reason: str = "",
    ) -> WorkOrder:
        order = self.get(work_order_id)
        transition_status(order, to_status, changed_at=self.timestamp_provider(), changed_by=changed_by, reason=reason)
        validate_work_order(order)
        return order

    def transfer_department(
        self,
        work_order_id: str,
        to_department: Department,
        *,
        owner: str,
        changed_by: str,
        reason: str = "",
    ) -> WorkOrder:
        order = self.get(work_order_id)
        previous = Department(order.department)
        order.previous_department = previous.value
        order.department = to_department
        order.current_owner = owner
        order.department_history.append(
            DepartmentTransition(previous.value, to_department, owner, self.timestamp_provider(), changed_by, reason)
        )
        validate_work_order(order)
        return order
