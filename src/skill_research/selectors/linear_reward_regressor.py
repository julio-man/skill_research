"""Supervised linear reward regressor selector."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from skill_research.patches.types import PatchPool
from skill_research.selectors.base import BaseSelector, SelectorDecision
from skill_research.selectors.linear_features import FEATURE_NAMES, dot, patch_features
from skill_research.selectors.linear_model import OnlineRidgeModel, load_model
from skill_research.selectors.linucb import _patch_and_reward


class LinearRewardRegressorSelector(BaseSelector):
    """Select the patch with the highest predicted reward."""

    name = "linear_reward_regressor"

    def __init__(self, l2: float = 1.0):
        self.model = OnlineRidgeModel(len(FEATURE_NAMES), l2=l2)
        self._last_state: Any = {}

    def select(self, state: Any, patch_pool: PatchPool) -> SelectorDecision:
        if not patch_pool.patches:
            raise ValueError("No patches available")
        self._last_state = state or {}
        weights = self.model.weights()
        scores = {patch.patch_id: dot(weights, patch_features(patch, self._last_state)) for patch in patch_pool.patches}
        patch = max(patch_pool.patches, key=lambda item: (scores[item.patch_id], item.patch_id))
        decision = self._decision(patch_pool, patch, "linear_reward_regressor")
        return SelectorDecision(decision.action_index, decision.patch_id, decision.patch, decision.reason, scores=scores)

    def observe(self, transition: Any) -> None:
        patch, reward = _patch_and_reward(transition)
        if patch is not None and reward is not None:
            state = transition.get("state", self._last_state) if isinstance(transition, dict) else self._last_state
            self.model.update(patch_features(patch, state), float(reward))

    def save_state(self, path: Path) -> None:
        self.model.save(path, self.name)

    def load_state(self, path: Path) -> None:
        if path.exists():
            self.model, _payload = load_model(path)
