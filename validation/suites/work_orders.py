from __future__ import annotations

import copy
import json

from safe_artifact_writer import SafeArtifactWriter
from validation.contracts import Artifact, fail_check, pass_check, suite_from_checks
from validation.suites.helpers import suite_main
from work_orders import (
    AcceptanceCriterion,
    Complexity,
    Deliverable,
    Department,
    DuplicateWorkOrderIdError,
    InvalidLifecycleTransitionError,
    Priority,
    RiskLevel,
    WorkOrderContract,
    WorkOrderIdGenerator,
    WorkOrderManager,
    WorkOrderStatus,
    from_json,
    to_json,
    validate_work_order,
)
from work_orders.enums import DeliverableType
from work_orders.exceptions import WorkOrderValidationError
from work_orders.schema import WORK_ORDER_SCHEMA


FIXED_TIME = "2026-07-19T00:00:00+00:00"


def _sample_order(manager: WorkOrderManager):
    return manager.create(
        title="Implement Work Order Domain Model",
        objective="Define a structured engineering contract for AK Labs OS departments",
        description="Create the v0.4.1 Work Order foundation without changing runtime pipeline behavior.",
        created_by="Architect",
        current_owner="Architect",
        department=Department.ARCHITECT,
        priority=Priority.HIGH,
        risk_level=RiskLevel.MEDIUM,
        estimated_complexity=Complexity.M,
        repository="ak_labs_os",
        constraints=[
            "Do not introduce repository intelligence",
            "Preserve deterministic execution",
            "Do not make Work Orders mandatory in runtime yet",
        ],
        acceptance_criteria=[
            AcceptanceCriterion("AC-001", "Work Order IDs are deterministic", True),
            AcceptanceCriterion("AC-002", "Invalid lifecycle transitions are rejected", True),
        ],
        deliverables=[
            Deliverable(DeliverableType.CREATED_FILE, "Work Order domain package", "work_orders/"),
            Deliverable(DeliverableType.TEST, "Work Order validation suite", "validation/suites/work_orders.py"),
            Deliverable(DeliverableType.DOCUMENTATION, "Release summary update", "RELEASE_SUMMARY.md"),
            Deliverable(DeliverableType.REPORT, "Release validation report", "reports/latest.md"),
        ],
        dependencies=[],
        affected_components=["work_orders", "validation"],
        artifact_targets=["work_orders/*.py", "validation/suites/work_orders.py"],
        review_requirements=["Validate schema and lifecycle semantics"],
        validation_requirements=["Run work_orders suite", "Run release harness"],
        contract=WorkOrderContract(
            inputs=["User request", "AK Labs OS policy and validation context"],
            outputs=["Canonical Work Order JSON", "Lifecycle history"],
            preconditions=["Architect has converted request into structured scope"],
            postconditions=["Every department can consume the same structured contract"],
        ),
        metadata={"milestone": "v0.4.1"},
    )


def _fixed_manager(start: int = 1) -> WorkOrderManager:
    return WorkOrderManager(id_generator=WorkOrderIdGenerator(start), timestamp_provider=lambda: FIXED_TIME)


def _expect_validation_error(check_id: str, expected: str, order):
    try:
        validate_work_order(order)
    except WorkOrderValidationError as exc:
        return pass_check(check_id, expected, "; ".join(exc.errors), {"errors": exc.errors})
    return fail_check(check_id, expected, "validation passed unexpectedly", order.to_dict())


def run(ctx):
    checks = []
    artifacts = []

    generator = WorkOrderIdGenerator()
    ids = [generator.next_id(), generator.next_id(), generator.next_id()]
    checks.append(pass_check("id_generation", "Sequential deterministic IDs", ", ".join(ids))
                  if ids == ["WO-000001", "WO-000002", "WO-000003"]
                  else fail_check("id_generation", "Sequential deterministic IDs", ", ".join(ids)))

    manager = _fixed_manager()
    order = _sample_order(manager)

    try:
        validate_work_order(order)
        checks.append(pass_check("schema_validation", "Valid Work Order passes schema validation", order.id))
    except WorkOrderValidationError as exc:
        checks.append(fail_check("schema_validation", "Valid Work Order passes schema validation", str(exc), {"errors": exc.errors}))

    serialized = to_json(order)
    restored = from_json(serialized)
    checks.append(pass_check("json_serialization", "JSON serialization round-trips canonical schema", restored.id)
                  if restored.to_dict() == order.to_dict()
                  else fail_check("json_serialization", "JSON serialization round-trips canonical schema", json.dumps(restored.to_dict(), sort_keys=True)))

    lifecycle_ok = True
    try:
        manager.transition(order.id, WorkOrderStatus.APPROVED, changed_by="Architect", reason="scope approved")
        manager.transfer_department(order.id, Department.DEVELOPER, owner="Developer", changed_by="Architect", reason="implementation handoff")
        manager.transition(order.id, WorkOrderStatus.IN_PROGRESS, changed_by="Developer")
        manager.transition(order.id, WorkOrderStatus.READY_FOR_REVIEW, changed_by="Developer")
        manager.transfer_department(order.id, Department.REVIEWER, owner="Reviewer", changed_by="Developer", reason="ready for review")
        manager.transition(order.id, WorkOrderStatus.READY_FOR_VALIDATION, changed_by="Reviewer")
        manager.transfer_department(order.id, Department.VALIDATOR, owner="Validator", changed_by="Reviewer", reason="ready for validation")
        manager.transition(order.id, WorkOrderStatus.COMPLETED, changed_by="Validator")
        manager.transfer_department(order.id, Department.HISTORIAN, owner="Historian", changed_by="Validator", reason="record lifecycle")
        manager.transition(order.id, WorkOrderStatus.ARCHIVED, changed_by="Historian")
    except Exception as exc:
        lifecycle_ok = False
        checks.append(fail_check("lifecycle_transitions", "Valid deterministic lifecycle transitions complete", repr(exc)))
    if lifecycle_ok:
        status_path = " -> ".join(item.to_status.value if hasattr(item.to_status, "value") else item.to_status for item in order.status_history)
        checks.append(pass_check("lifecycle_transitions", "Valid deterministic lifecycle transitions complete", status_path))

    bad_transition_manager = _fixed_manager()
    bad_order = _sample_order(bad_transition_manager)
    try:
        bad_transition_manager.transition(bad_order.id, WorkOrderStatus.COMPLETED, changed_by="Validator")
    except InvalidLifecycleTransitionError as exc:
        checks.append(pass_check("invalid_transition_rejected", "Invalid lifecycle transitions are rejected", str(exc)))
    else:
        checks.append(fail_check("invalid_transition_rejected", "Invalid lifecycle transitions are rejected", "transition allowed"))

    duplicate_manager = _fixed_manager()
    duplicate_order = _sample_order(duplicate_manager)
    try:
        duplicate_manager.add(duplicate_order)
    except DuplicateWorkOrderIdError as exc:
        checks.append(pass_check("duplicate_id_rejected", "Duplicate Work Order IDs are rejected", str(exc)))
    else:
        checks.append(fail_check("duplicate_id_rejected", "Duplicate Work Order IDs are rejected", "duplicate accepted"))

    missing_title = copy.deepcopy(order)
    missing_title.title = ""
    checks.append(_expect_validation_error("missing_title_rejected", "Missing title is rejected", missing_title))

    missing_objective = copy.deepcopy(order)
    missing_objective.objective = ""
    checks.append(_expect_validation_error("missing_objective_rejected", "Missing objective is rejected", missing_objective))

    missing_acceptance = copy.deepcopy(order)
    missing_acceptance.acceptance_criteria = []
    checks.append(_expect_validation_error("missing_acceptance_criteria_rejected", "Missing acceptance criteria are rejected", missing_acceptance))

    invalid_priority = copy.deepcopy(order)
    invalid_priority.priority = "URGENT"
    checks.append(_expect_validation_error("invalid_priority_rejected", "Invalid priority is rejected", invalid_priority))

    ac_ok = [criterion.to_dict() for criterion in order.acceptance_criteria]
    checks.append(pass_check("acceptance_criteria_structured", "Acceptance criteria are structured objects", json.dumps(ac_ok, sort_keys=True))
                  if ac_ok and all({"id", "description", "mandatory"} <= set(item) for item in ac_ok)
                  else fail_check("acceptance_criteria_structured", "Acceptance criteria are structured objects", json.dumps(ac_ok)))

    deliverable_types = sorted({deliverable.type.value for deliverable in order.deliverables})
    expected_deliverables = sorted([
        DeliverableType.CREATED_FILE.value,
        DeliverableType.TEST.value,
        DeliverableType.DOCUMENTATION.value,
        DeliverableType.REPORT.value,
    ])
    checks.append(pass_check("deliverables_supported", "Deliverables support created files, tests, documentation, and reports", ", ".join(deliverable_types))
                  if deliverable_types == expected_deliverables
                  else fail_check("deliverables_supported", "Deliverables support required categories", ", ".join(deliverable_types)))

    constraints_ok = "Preserve deterministic execution" in order.constraints
    checks.append(pass_check("constraints_supported", "Multiple engineering constraints are preserved", json.dumps(order.constraints))
                  if constraints_ok else fail_check("constraints_supported", "Multiple engineering constraints are preserved", json.dumps(order.constraints)))

    contract = order.contract.to_dict()
    contract_ok = all(contract[key] for key in ("inputs", "outputs", "preconditions", "postconditions"))
    checks.append(pass_check("work_order_contract_supported", "Work Order contract contains inputs, outputs, preconditions, postconditions", json.dumps(contract, sort_keys=True))
                  if contract_ok else fail_check("work_order_contract_supported", "Work Order contract contains required sections", json.dumps(contract, sort_keys=True)))

    ownership_ok = (
        order.department == Department.HISTORIAN
        and order.previous_department == Department.VALIDATOR.value
        and [item.to_department.value for item in order.department_history]
        == [
            Department.ARCHITECT.value,
            Department.DEVELOPER.value,
            Department.REVIEWER.value,
            Department.VALIDATOR.value,
            Department.HISTORIAN.value,
        ]
    )
    checks.append(pass_check("department_ownership_history", "Department ownership and history are preserved", json.dumps([item.to_dict() for item in order.department_history], sort_keys=True))
                  if ownership_ok else fail_check("department_ownership_history", "Department ownership and history are preserved", json.dumps(order.to_dict(), sort_keys=True)))

    schema_ok = WORK_ORDER_SCHEMA["schema_version"] == 1 and WORK_ORDER_SCHEMA["serialization"]["yaml"] == "reserved for future support"
    checks.append(pass_check("schema_versioning", "Schema version is present and YAML is reserved, not implemented", json.dumps(WORK_ORDER_SCHEMA, sort_keys=True))
                  if schema_ok else fail_check("schema_versioning", "Schema versioning and future YAML reservation exist", json.dumps(WORK_ORDER_SCHEMA, sort_keys=True)))

    artifact_path = SafeArtifactWriter(ctx.workspace).write_text(
        "work_orders/example_work_order.json",
        to_json(order),
        origin="validator",
    )
    artifacts.append(Artifact("example_work_order", str(artifact_path), "Canonical Work Order JSON example"))

    return suite_from_checks("work_orders", checks, artifacts=artifacts)


if __name__ == "__main__":
    suite_main("work_orders")
