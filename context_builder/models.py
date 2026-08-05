from dataclasses import dataclass

@dataclass(frozen=True)
class EngineeringContext:
    summary: str
    repository_type: str
    technology_stack: dict
    entry_points: list[str]
    primary_files: list[str]
    supporting_files: list[str]
    reference_files: list[str]
    constraints: list[str]
    acceptance_criteria: list[dict]
    deliverables: list[dict]
    relevant_tests: list[str]
    known_risks: list[str]
    engineering_notes: list[str]
    selection_confidence: float
    context_version: int = 1
    context_schema_version: str = "1.0"