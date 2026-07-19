from __future__ import annotations

import re
from typing import Iterable

from work_orders.enums import Complexity, DeliverableType, Department, Priority, RiskLevel, WorkOrderStatus
from work_orders.exceptions import WorkOrderValidationError
from work_orders.ids import validate_work_order_id
from work_orders.models import SCHEMA_VERSION, WorkOrder
from work_orders.schema import REQUIRED_FIELDS


AC_ID_PATTERN = re.compile(r"^AC-\d{3}$")


def _require_non_empty_string(errors: list[str], name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{name} is required")


def _require_string_list(errors: list[str], name: str, values: object) -> None:
    if not isinstance(values, list):
        errors.append(f"{name} must be a list")
        return
    if not all(isinstance(item, str) and item.strip() for item in values):
        errors.append(f"{name} must contain only non-empty strings")


def collect_validation_errors(work_order: WorkOrder, existing_ids: Iterable[str] | None = None) -> list[str]:
    errors: list[str] = []
    data = work_order.to_dict()

    missing = [field for field in REQUIRED_FIELDS if field not in data]
    if missing:
        errors.append("missing required field(s): " + ", ".join(missing))

    if work_order.schema_version != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if not validate_work_order_id(work_order.id):
        errors.append("id must match WO-000001 format")
    if existing_ids and work_order.id in set(existing_ids):
        errors.append(f"duplicate work order id: {work_order.id}")

    _require_non_empty_string(errors, "title", work_order.title)
    _require_non_empty_string(errors, "objective", work_order.objective)
    _require_non_empty_string(errors, "created_at", work_order.created_at)
    _require_non_empty_string(errors, "created_by", work_order.created_by)
    _require_non_empty_string(errors, "current_owner", work_order.current_owner)

    try:
        Priority(work_order.priority)
    except ValueError:
        errors.append("priority is invalid")
    try:
        WorkOrderStatus(work_order.status)
    except ValueError:
        errors.append("status is invalid")
    try:
        RiskLevel(work_order.risk_level)
    except ValueError:
        errors.append("risk_level is invalid")
    try:
        Complexity(work_order.estimated_complexity)
    except ValueError:
        errors.append("estimated_complexity is invalid")
    try:
        Department(work_order.department)
    except ValueError:
        errors.append("department is invalid")

    _require_string_list(errors, "constraints", work_order.constraints)
    _require_string_list(errors, "dependencies", work_order.dependencies)
    _require_string_list(errors, "affected_components", work_order.affected_components)
    _require_string_list(errors, "artifact_targets", work_order.artifact_targets)
    _require_string_list(errors, "review_requirements", work_order.review_requirements)
    _require_string_list(errors, "validation_requirements", work_order.validation_requirements)

    if not work_order.acceptance_criteria:
        errors.append("acceptance_criteria must contain at least one item")
    ac_ids = set()
    for criterion in work_order.acceptance_criteria:
        if not AC_ID_PATTERN.fullmatch(criterion.id):
            errors.append(f"acceptance criterion id is invalid: {criterion.id}")
        if criterion.id in ac_ids:
            errors.append(f"duplicate acceptance criterion id: {criterion.id}")
        ac_ids.add(criterion.id)
        _require_non_empty_string(errors, f"acceptance criterion {criterion.id} description", criterion.description)
        if not isinstance(criterion.mandatory, bool):
            errors.append(f"acceptance criterion {criterion.id} mandatory must be boolean")

    for deliverable in work_order.deliverables:
        try:
            DeliverableType(deliverable.type)
        except ValueError:
            errors.append(f"deliverable type is invalid: {deliverable.type}")
        _require_non_empty_string(errors, "deliverable description", deliverable.description)
        if not isinstance(deliverable.mandatory, bool):
            errors.append("deliverable mandatory must be boolean")

    contract = work_order.contract
    _require_string_list(errors, "contract.inputs", contract.inputs)
    _require_string_list(errors, "contract.outputs", contract.outputs)
    _require_string_list(errors, "contract.preconditions", contract.preconditions)
    _require_string_list(errors, "contract.postconditions", contract.postconditions)

    if not isinstance(work_order.metadata, dict):
        errors.append("metadata must be an object")

    return errors


def validate_work_order(work_order: WorkOrder, existing_ids: Iterable[str] | None = None) -> None:
    errors = collect_validation_errors(work_order, existing_ids)
    if errors:
        raise WorkOrderValidationError(errors)
