from dataclasses import dataclass, field
from enum import Enum
from typing import Any

class RuleImportance(str, Enum):
    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"
    OPTIONAL = "OPTIONAL"

    def __str__(self) -> str:
        return self.value

@dataclass
class RuleTrace:
    stage: int
    rule_name: str
    importance: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    explanation: str
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "rule_name": self.rule_name,
            "importance": self.importance,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "explanation": self.explanation
        }

@dataclass
class FileSelection:
    primary_files: list[str] = field(default_factory=list)
    supporting_files: list[str] = field(default_factory=list)
    reference_files: list[str] = field(default_factory=list)
    excluded_files: list[str] = field(default_factory=list)
    traces: list[RuleTrace] = field(default_factory=list)
    confidence: float = 0.0
    confidence_breakdown: dict[str, float] = field(default_factory=dict)
    status: str = "resolved"  # "resolved" | "needs_review"
    escalation_reason: str | None = None
    selection_version: str = "1.0"