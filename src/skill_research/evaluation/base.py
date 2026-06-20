from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CheckResult:
    kind: str
    passed: bool
    message: str
    details: dict[str, Any]


@dataclass
class EvaluationResult:
    passed: bool
    score: float
    failure_type: str
    checks: list[CheckResult]
    metadata: dict[str, Any]
