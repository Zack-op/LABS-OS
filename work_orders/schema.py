from __future__ import annotations

from work_orders.enums import Complexity, Department, DeliverableType, Priority, RiskLevel, WorkOrderStatus
from work_orders.models import SCHEMA_VERSION


REQUIRED_FIELDS = (
    "schema_version",
    "id",
    "title",
    "objective",
    "description",
    "priority",
    "status",
    "created_at",
    "created_by",
    "current_owner",
    "department",
    "repository",
    "constraints",
    "acceptance_criteria",
    "deliverables",
    "dependencies",
    "affected_components",
    "artifact_targets",
    "review_requirements",
    "validation_requirements",
    "risk_level",
    "estimated_complexity",
    "contract",
    "metadata",
    "status_history",
    "department_history",
)


WORK_ORDER_SCHEMA = {
    "schema_version": SCHEMA_VERSION,
    "required": list(REQUIRED_FIELDS),
    "enums": {
        "priority": [item.value for item in Priority],
        "status": [item.value for item in WorkOrderStatus],
        "risk_level": [item.value for item in RiskLevel],
        "estimated_complexity": [item.value for item in Complexity],
        "department": [item.value for item in Department],
        "deliverable_type": [item.value for item in DeliverableType],
    },
    "contract": {
        "inputs": "list[str]",
        "outputs": "list[str]",
        "preconditions": "list[str]",
        "postconditions": "list[str]",
    },
    "serialization": {
        "json": "implemented",
        "yaml": "reserved for future support",
    },
}
