from __future__ import annotations

from skill_research.patches.types import PatchPool
from skill_research.selectors.base import BaseSelector, SelectorDecision


class SupportCountSelector(BaseSelector):
    name = "support_count"

    def select(self, state, patch_pool: PatchPool) -> SelectorDecision:
        patch = max(patch_pool.patches, key=lambda item: (item.support_count, -item.delta_tokens, item.patch_id))
        return self._decision(patch_pool, patch, "support_count")
