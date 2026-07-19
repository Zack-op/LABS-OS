from __future__ import annotations

import re


WORK_ORDER_ID_PATTERN = re.compile(r"^WO-\d{6}$")


def validate_work_order_id(work_order_id: str) -> bool:
    return bool(WORK_ORDER_ID_PATTERN.fullmatch(work_order_id))


def parse_work_order_number(work_order_id: str) -> int:
    if not validate_work_order_id(work_order_id):
        raise ValueError(f"invalid work order id: {work_order_id}")
    return int(work_order_id.split("-", 1)[1])


class WorkOrderIdGenerator:
    def __init__(self, start: int = 1):
        if start < 1:
            raise ValueError("Work Order IDs start at 1")
        self._next = start

    def next_id(self) -> str:
        value = f"WO-{self._next:06d}"
        self._next += 1
        return value

    def reserve(self, work_order_id: str) -> None:
        number = parse_work_order_number(work_order_id)
        if number >= self._next:
            self._next = number + 1

    @property
    def next_number(self) -> int:
        return self._next
