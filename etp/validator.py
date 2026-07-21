from __future__ import annotations
from etp.exceptions import ETPValidationError
from etp.models import TransactionRecord, EvidencePackage
from etp.enums import TransactionOutcome, TransferIntent

def validate_transaction(tx: TransactionRecord) -> None:
    """
    Validates the protocol invariants of the ETP envelope.
    Does NOT validate engineering correctness, policy, or Work Order state.
    """
    errors = []

    # Required Metadata Invariants
    if not tx.protocol_version:
        errors.append("Missing protocol_version")
    if not tx.transaction_id:
        errors.append("Missing transaction_id")
    if tx.sequence_number < 1:
        errors.append("Sequence number must be 1 or greater")
    if not tx.work_order_id:
        errors.append("Missing work_order_id (one Work Order per transaction)")
        
    # Department & Ownership Invariants
    if not tx.source_department or not tx.source_owner:
        errors.append("Missing explicit source department and owner")
    if not tx.destination_department or not tx.destination_owner:
        errors.append("Missing explicit destination department and owner")
    if not tx.initiated_by:
        errors.append("Missing initiated_by actor")

    # Intent Invariant
    intent_str = getattr(tx.transfer_intent, "value", tx.transfer_intent)
    if intent_str not in {intent.value for intent in TransferIntent}:
        errors.append(f"Invalid transfer_intent: {intent_str}")

    # Evidence Invariants
    if not tx.evidence_refs:
        errors.append("Missing evidence package")
    elif not isinstance(tx.evidence_refs, EvidencePackage):
        errors.append("evidence_refs must be an EvidencePackage instance")
    else:
        if not tx.evidence_refs.work_order_ref:
            errors.append("Evidence must contain work_order_ref")
        if not tx.evidence_refs.completion_statement:
            errors.append("Evidence must contain source completion_statement")
        if not tx.evidence_refs.readiness_basis:
            errors.append("Evidence must contain destination readiness_basis")

    # Transaction Outcome Invariants
    outcome_str = getattr(tx.outcome, "value", tx.outcome)
    if outcome_str not in (TransactionOutcome.ACCEPTED.value, TransactionOutcome.REJECTED.value):
        errors.append(f"Invalid outcome: {outcome_str}")

    if outcome_str == TransactionOutcome.ACCEPTED.value:
        if tx.active_owner_after != tx.destination_owner:
            errors.append("Accepted transfer must assign active_owner_after to destination_owner")
    elif outcome_str == TransactionOutcome.REJECTED.value:
        if tx.active_owner_after != tx.source_owner:
            errors.append("Rejected transfer must leave active_owner_after as source_owner")

    if errors:
        raise ETPValidationError(errors)