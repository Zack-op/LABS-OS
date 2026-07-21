from __future__ import annotations

class ETPError(Exception):
    """Base exception for Engineering Transaction Protocol failures."""

class ETPValidationError(ETPError):
    """Raised when a transaction envelope violates ETP invariants."""
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))

class OutOfSequenceError(ETPError):
    """Raised when replaying transactions that break deterministic sequencing."""