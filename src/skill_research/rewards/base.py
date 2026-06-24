"""Common reward result dataclass and reward-function protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class RewardResult:
    value: float
    score_delta: float
    pass_rate_delta: float
    token_growth: int = 0
    anchor_regressions: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class RewardFunction(Protocol):
    name: str

    def compute(self, before, after, context: dict) -> RewardResult:
        ...
