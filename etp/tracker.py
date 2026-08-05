from __future__ import annotations
from etp.enums import TransferIntent
from etp.models import EvidencePackage, TransactionRecord
from etp.transaction import evaluate_transfer

class ETPTracker:
    """
    Statefully tracks ETP transaction sequencing and linkage only.
    Derives department ownership explicitly from the caller to prevent 
    duplicate state ownership.
    """
    def __init__(self, protocol_version: str):
        self.protocol_version = protocol_version
        self.sequence_number = 0
        self.previous_transaction_id = None

    def attempt_transfer(
        self, 
        work_order_id: str,
        current_department: str,
        destination_department: str, 
        intent: TransferIntent | str, 
        reason: str, 
        reject_reason: str | None = None,
        deliverable_refs: list[str] | None = None
    ) -> TransactionRecord:
        self.sequence_number += 1
        transaction_id = f"TX-{work_order_id}-{self.sequence_number:03d}"
        
        evidence = EvidencePackage(
            work_order_ref=work_order_id,
            completion_statement=f"{current_department} phase complete",
            readiness_basis=f"{destination_department} ready to receive" if not reject_reason else "Blocked by pipeline policy",
            deliverable_refs=deliverable_refs or []
        )
        
        tx = evaluate_transfer(
            protocol_version=self.protocol_version,
            transaction_id=transaction_id,
            sequence_number=self.sequence_number,
            work_order_id=work_order_id,
            source_department=current_department,
            source_owner=current_department,
            destination_department=destination_department,
            destination_owner=destination_department,
            initiated_by=current_department,
            transfer_reason=reason,
            transfer_intent=intent,
            evidence=evidence,
            previous_transaction_id=self.previous_transaction_id,
            reject_reason=reject_reason
        )
        
        self.previous_transaction_id = tx.transaction_id
        return tx