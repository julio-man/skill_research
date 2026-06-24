from __future__ import annotations

from skill_research.patches.types import PatchPool
from skill_research.selectors.base import BaseSelector, SelectorDecision


class GreedySelector(BaseSelector):
    name = "greedy"

    def select(self, state, patch_pool: PatchPool) -> SelectorDecision:
        scores = state.get("validation_scores", {}) if isinstance(state, dict) else {}
        if not scores:
            raise ValueError("GreedySelector requires validation_scores")
        patch_id = max(scores, key=lambda item: (scores[item], item))
        patch = next(patch for patch in patch_pool.patches if patch.patch_id == patch_id)
        decision = self._decision(patch_pool, patch, "greedy_validation")
        return SelectorDecision(decision.action_index, decision.patch_id, decision.patch, decision.reason, scores=scores)
