from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TraceRecord:
    task_id: str
    success: bool
    failure_type: str
    payload: dict[str, Any] = field(default_factory=dict)
