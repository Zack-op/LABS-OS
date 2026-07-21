from __future__ import annotations
from typing import Iterable

from etp.enums import TransactionOutcome
from etp.exceptions import OutOfSequenceError
from etp.models import TransactionRecord

def replay_ownership(transactions: Iterable[TransactionRecord]) -> dict[str, str]:
    """
    Replays an append-only transaction history to reconstruct the active owner 
    for all tracked Work Orders, enforcing deterministic sequencing.
    """
    active_owners: dict[str, str] = {}
    sequences: dict[str, int] = {}
    
    sorted_txs = sorted(transactions, key=lambda x: x.sequence_number)
    
    for tx in sorted_txs:
        wo_id = tx.work_order_id
        
        # Sequence must be strictly sequential per Work Order or globally (depending on generation strategy). 
        # Here we validate sequence numbers increment correctly per Work Order history.
        expected_seq = sequences.get(wo_id, 0) + 1
        if tx.sequence_number != expected_seq:
            raise OutOfSequenceError(
                f"Sequence break for {wo_id}: expected {expected_seq}, got {tx.sequence_number}"
            )
        
        sequences[wo_id] = tx.sequence_number
        
        # Only accepted transactions transfer ownership
        outcome_str = getattr(tx.outcome, "value", tx.outcome)
        if outcome_str == TransactionOutcome.ACCEPTED.value:
            active_owners[wo_id] = tx.active_owner_after
            
    return active_owners