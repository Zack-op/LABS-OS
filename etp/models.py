from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from etp.enums import TransactionOutcome, TransferIntent

@dataclass
class EvidencePackage:
    """Minimum evidence required to justify an ownership transfer."""
    work_order_ref: str
    completion_statement: str
    readiness_basis: str
    deliverable_refs: list[str] = field(default_factory=list)
    review_refs: list[str] = field(default_factory=list)
    validation_refs: list[str] = field(default_factory=list)
    policy_refs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_order_ref": self.work_order_ref,
            "completion_statement": self.completion_statement,
            "readiness_basis": self.readiness_basis,
            "deliverable_refs": list(self.deliverable_refs),
            "review_refs": list(self.review_refs),
            "validation_refs": list(self.validation_refs),
            "policy_refs": list(self.policy_refs),
        }

@dataclass
class TransactionRecord:
    """The canonical Engineering Transaction Protocol envelope."""
    protocol_version: str
    transaction_id: str
    sequence_number: int
    work_order_id: str
    source_department: str
    source_owner: str
    destination_department: str
    destination_owner: str
    initiated_by: str
    transfer_reason: str
    transfer_intent: TransferIntent | str
    previous_transaction_id: str | None
    outcome: TransactionOutcome | str
    outcome_reason: str
    active_owner_after: str
    evidence_refs: EvidencePackage
    policy_refs: list[str] = field(default_factory=list)
    validation_refs: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "protocol_version": self.protocol_version,
            "transaction_id": self.transaction_id,
            "sequence_number": self.sequence_number,
            "work_order_id": self.work_order_id,
            "source_department": self.source_department,
            "source_owner": self.source_owner,
            "destination_department": self.destination_department,
            "destination_owner": self.destination_owner,
            "initiated_by": self.initiated_by,
            "transfer_reason": self.transfer_reason,
            "transfer_intent": getattr(self.transfer_intent, "value", self.transfer_intent),
            "previous_transaction_id": self.previous_transaction_id,
            "outcome": getattr(self.outcome, "value", self.outcome),
            "outcome_reason": self.outcome_reason,
            "active_owner_after": self.active_owner_after,
            "evidence_refs": self.evidence_refs.to_dict(),
            "policy_refs": list(self.policy_refs),
            "validation_refs": list(self.validation_refs),
            "created_at": self.created_at,
        }