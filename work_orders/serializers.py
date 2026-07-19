from __future__ import annotations

import json

from work_orders.models import WorkOrder
from work_orders.validator import validate_work_order


def to_json(work_order: WorkOrder, *, pretty: bool = True, validate: bool = True) -> str:
    if validate:
        validate_work_order(work_order)
    indent = 2 if pretty else None
    return json.dumps(work_order.to_dict(), indent=indent, sort_keys=True)


def from_json(payload: str, *, validate: bool = True) -> WorkOrder:
    data = json.loads(payload)
    work_order = WorkOrder.from_dict(data)
    if validate:
        validate_work_order(work_order)
    return work_order
