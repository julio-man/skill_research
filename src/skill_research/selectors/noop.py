from __future__ import annotations

from skill_research.patches.types import PatchPool
from skill_research.selectors.base import BaseSelector, SelectorDecision


class NoOpSelector(BaseSelector):
    name = "noop"

    def select(self, state, patch_pool: PatchPool) -> SelectorDecision:
        return SelectorDecision(action_index=None, patch_id="noop", patch=None, reason="noop")
