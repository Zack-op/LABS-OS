from __future__ import annotations
from datetime import datetime, timezone
from typing import Iterable

from etp.enums import TransactionOutcome, TransferIntent
from etp.models import EvidencePackage, TransactionRecord
from etp.validator import validate_transaction

def evaluate_transfer(
    protocol_version: str,
    transaction_id: str,
    sequence_number: int,
    work_order_id: str,
    source_department: str,
    source_owner: str,
    destination_department: str,
    destination_owner: str,
    initiated_by: str,
    transfer_reason: str,
    transfer_intent: TransferIntent | str,
    evidence: EvidencePackage,
    previous_transaction_id: str | None = None,
    policy_refs: Iterable[str] | None = None,
    validation_refs: Iterable[str] | None = None,
    reject_reason: str | None = None,
    timestamp_provider=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
) -> TransactionRecord:
    """
    Evaluates a transfer intent and produces a canonical transaction record.
    If a reject_reason is provided (e.g., from an upstream policy failure), 
    the transaction is recorded as REJECTED and ownership remains with the source.
    """
    outcome = TransactionOutcome.REJECTED if reject_reason else TransactionOutcome.ACCEPTED
    outcome_reason = reject_reason or "Transfer criteria met and accepted"
    
    # Ownership determination rule: Rejected transactions do not change active ownership.
    active_owner = source_owner if outcome == TransactionOutcome.REJECTED else destination_owner

    tx = TransactionRecord(
        protocol_version=protocol_version,
        transaction_id=transaction_id,
        sequence_number=sequence_number,
        work_order_id=work_order_id,
        source_department=source_department,
        source_owner=source_owner,
        destination_department=destination_department,
        destination_owner=destination_owner,
        initiated_by=initiated_by,
        transfer_reason=transfer_reason,
        transfer_intent=transfer_intent,
        previous_transaction_id=previous_transaction_id,
        outcome=outcome,
        outcome_reason=outcome_reason,
        active_owner_after=active_owner,
        evidence_refs=evidence,
        policy_refs=list(policy_refs or []),
        validation_refs=list(validation_refs or []),
        created_at=timestamp_provider()
    )
    
    validate_transaction(tx)
    return tx