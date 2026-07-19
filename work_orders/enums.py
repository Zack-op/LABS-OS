from __future__ import annotations

from enum import Enum


class StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class WorkOrderStatus(StringEnum):
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IN_PROGRESS = "IN_PROGRESS"
    READY_FOR_REVIEW = "READY_FOR_REVIEW"
    REVIEW_FAILED = "REVIEW_FAILED"
    READY_FOR_VALIDATION = "READY_FOR_VALIDATION"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class Priority(StringEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Complexity(StringEnum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"


class RiskLevel(StringEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Department(StringEnum):
    ARCHITECT = "Architect"
    DEVELOPER = "Developer"
    REVIEWER = "Reviewer"
    VALIDATOR = "Validator"
    HISTORIAN = "Historian"


class DeliverableType(StringEnum):
    CREATED_FILE = "created_file"
    MODIFIED_FILE = "modified_file"
    DOCUMENTATION = "documentation"
    TEST = "test"
    REPORT = "report"
