from __future__ import annotations
from enum import Enum

class StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value

class TransactionOutcome(StringEnum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"

class TransferIntent(StringEnum):
    REVIEW = "REVIEW"
    REWORK = "REWORK"
    VALIDATE = "VALIDATE"
    COMPLETE = "COMPLETE"
    HANDOFF = "HANDOFF"