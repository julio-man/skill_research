"""Seeded random patch selector baseline."""

from __future__ import annotations

import random

from skill_research.patches.types import PatchPool
from skill_research.selectors.base import BaseSelector, SelectorDecision


class RandomSelector(BaseSelector):
    name = "random"

    def __init__(self, seed: int = 42):
        self._random = random.Random(seed)

    def select(self, state, patch_pool: PatchPool) -> SelectorDecision:
        if not patch_pool.patches:
            raise ValueError("No patches available")
        patch = self._random.choice(patch_pool.patches)
        return self._decision(patch_pool, patch, "random")
