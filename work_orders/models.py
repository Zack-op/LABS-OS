from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from work_orders.enums import Complexity, DeliverableType, Department, Priority, RiskLevel, WorkOrderStatus


SCHEMA_VERSION = 1


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


@dataclass
class AcceptanceCriterion:
    id: str
    description: str
    mandatory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "description": self.description, "mandatory": self.mandatory}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AcceptanceCriterion":
        return cls(id=str(data.get("id", "")), description=str(data.get("description", "")), mandatory=bool(data.get("mandatory", True)))


@dataclass
class Deliverable:
    type: DeliverableType | str
    description: str
    path: str = ""
    mandatory: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": _enum_value(self.type),
            "description": self.description,
            "path": self.path,
            "mandatory": self.mandatory,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Deliverable":
        return cls(
            type=DeliverableType(data.get("type")),
            description=str(data.get("description", "")),
            path=str(data.get("path", "")),
            mandatory=bool(data.get("mandatory", True)),
        )


@dataclass
class WorkOrderContract:
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    postconditions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "preconditions": list(self.preconditions),
            "postconditions": list(self.postconditions),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "WorkOrderContract":
        data = data or {}
        return cls(
            inputs=list(data.get("inputs", [])),
            outputs=list(data.get("outputs", [])),
            preconditions=list(data.get("preconditions", [])),
            postconditions=list(data.get("postconditions", [])),
        )


@dataclass
class StatusTransition:
    from_status: str | None
    to_status: WorkOrderStatus | str
    changed_at: str
    changed_by: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_status": self.from_status,
            "to_status": _enum_value(self.to_status),
            "changed_at": self.changed_at,
            "changed_by": self.changed_by,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StatusTransition":
        return cls(
            from_status=data.get("from_status"),
            to_status=WorkOrderStatus(data.get("to_status")),
            changed_at=str(data.get("changed_at", "")),
            changed_by=str(data.get("changed_by", "")),
            reason=str(data.get("reason", "")),
        )


@dataclass
class DepartmentTransition:
    from_department: str | None
    to_department: Department | str
    owner: str
    changed_at: str
    changed_by: str
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_department": self.from_department,
            "to_department": _enum_value(self.to_department),
            "owner": self.owner,
            "changed_at": self.changed_at,
            "changed_by": self.changed_by,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DepartmentTransition":
        return cls(
            from_department=data.get("from_department"),
            to_department=Department(data.get("to_department")),
            owner=str(data.get("owner", "")),
            changed_at=str(data.get("changed_at", "")),
            changed_by=str(data.get("changed_by", "")),
            reason=str(data.get("reason", "")),
        )


@dataclass
class WorkOrder:
    id: str
    title: str
    objective: str
    description: str
    priority: Priority | str
    status: WorkOrderStatus | str
    created_at: str
    created_by: str
    current_owner: str
    department: Department | str
    repository: str = ""
    constraints: list[str] = field(default_factory=list)
    acceptance_criteria: list[AcceptanceCriterion] = field(default_factory=list)
    deliverables: list[Deliverable] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    affected_components: list[str] = field(default_factory=list)
    artifact_targets: list[str] = field(default_factory=list)
    review_requirements: list[str] = field(default_factory=list)
    validation_requirements: list[str] = field(default_factory=list)
    risk_level: RiskLevel | str = RiskLevel.LOW
    estimated_complexity: Complexity | str = Complexity.M
    contract: WorkOrderContract = field(default_factory=WorkOrderContract)
    metadata: dict[str, Any] = field(default_factory=dict)
    previous_department: str | None = None
    status_history: list[StatusTransition] = field(default_factory=list)
    department_history: list[DepartmentTransition] = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "id": self.id,
            "title": self.title,
            "objective": self.objective,
            "description": self.description,
            "priority": _enum_value(self.priority),
            "status": _enum_value(self.status),
            "created_at": self.created_at,
            "created_by": self.created_by,
            "current_owner": self.current_owner,
            "department": _enum_value(self.department),
            "previous_department": self.previous_department,
            "repository": self.repository,
            "constraints": list(self.constraints),
            "acceptance_criteria": [criterion.to_dict() for criterion in self.acceptance_criteria],
            "deliverables": [deliverable.to_dict() for deliverable in self.deliverables],
            "dependencies": list(self.dependencies),
            "affected_components": list(self.affected_components),
            "artifact_targets": list(self.artifact_targets),
            "review_requirements": list(self.review_requirements),
            "validation_requirements": list(self.validation_requirements),
            "risk_level": _enum_value(self.risk_level),
            "estimated_complexity": _enum_value(self.estimated_complexity),
            "contract": self.contract.to_dict(),
            "metadata": dict(self.metadata),
            "status_history": [transition.to_dict() for transition in self.status_history],
            "department_history": [transition.to_dict() for transition in self.department_history],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkOrder":
        return cls(
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            id=str(data.get("id", "")),
            title=str(data.get("title", "")),
            objective=str(data.get("objective", "")),
            description=str(data.get("description", "")),
            priority=Priority(data.get("priority")),
            status=WorkOrderStatus(data.get("status")),
            created_at=str(data.get("created_at", "")),
            created_by=str(data.get("created_by", "")),
            current_owner=str(data.get("current_owner", data.get("created_by", ""))),
            department=Department(data.get("department")),
            previous_department=data.get("previous_department"),
            repository=str(data.get("repository", "")),
            constraints=list(data.get("constraints", [])),
            acceptance_criteria=[AcceptanceCriterion.from_dict(item) for item in data.get("acceptance_criteria", [])],
            deliverables=[Deliverable.from_dict(item) for item in data.get("deliverables", [])],
            dependencies=list(data.get("dependencies", [])),
            affected_components=list(data.get("affected_components", [])),
            artifact_targets=list(data.get("artifact_targets", [])),
            review_requirements=list(data.get("review_requirements", [])),
            validation_requirements=list(data.get("validation_requirements", [])),
            risk_level=RiskLevel(data.get("risk_level")),
            estimated_complexity=Complexity(data.get("estimated_complexity")),
            contract=WorkOrderContract.from_dict(data.get("contract")),
            metadata=dict(data.get("metadata", {})),
            status_history=[StatusTransition.from_dict(item) for item in data.get("status_history", [])],
            department_history=[DepartmentTransition.from_dict(item) for item in data.get("department_history", [])],
        )
