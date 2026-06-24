"""Heuristic selector that prefers the smallest non-noop patch."""

from __future__ import annotations

from skill_research.patches.types import PatchPool
from skill_research.selectors.base import BaseSelector, SelectorDecision


class SmallestPatchSelector(BaseSelector):
    name = "smallest_patch"

    def select(self, state, patch_pool: PatchPool) -> SelectorDecision:
        candidates = [patch for patch in patch_pool.patches if patch.operation != "no_op" and patch.patch_id != "noop"]
        if not candidates:
            candidates = patch_pool.patches
        patch = min(candidates, key=lambda item: (item.delta_tokens, -item.support_count, item.patch_id))
        return self._decision(patch_pool, patch, "smallest_patch")
