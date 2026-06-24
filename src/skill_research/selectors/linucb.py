"""LinUCB selector for contextual patch selection."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from skill_research.patches.types import Patch, PatchPool
from skill_research.selectors.base import BaseSelector, SelectorDecision
from skill_research.selectors.linear_features import FEATURE_NAMES, dot, patch_features
from skill_research.selectors.linear_model import OnlineRidgeModel, load_model


class LinUCBSelector(BaseSelector):
    """Select patches using an online linear UCB score."""

    name = "linucb"

    def __init__(self, alpha: float = 1.0, l2: float = 1.0):
        self.alpha = alpha
        self.model = OnlineRidgeModel(len(FEATURE_NAMES), l2=l2)
        self._last_state: Any = {}

    def select(self, state: Any, patch_pool: PatchPool) -> SelectorDecision:
        if not patch_pool.patches:
            raise ValueError("No patches available")
        self._last_state = state or {}
        weights = self.model.weights()
        scores = {}
        for patch in patch_pool.patches:
            features = patch_features(patch, state)
            scores[patch.patch_id] = dot(weights, features) + self.alpha * math.sqrt(max(self.model.variance(features), 0.0))
        patch = max(patch_pool.patches, key=lambda item: (scores[item.patch_id], item.patch_id))
        decision = self._decision(patch_pool, patch, "linucb")
        return SelectorDecision(decision.action_index, decision.patch_id, decision.patch, decision.reason, scores=scores)

    def observe(self, transition: Any) -> None:
        patch, reward = _patch_and_reward(transition)
        if patch is not None and reward is not None:
            state = transition.get("state", self._last_state) if isinstance(transition, dict) else self._last_state
            self.model.update(patch_features(patch, state), float(reward))

    def save_state(self, path: Path) -> None:
        self.model.save(path, self.name, {"alpha": self.alpha})

    def load_state(self, path: Path) -> None:
        if path.exists():
            model, payload = load_model(path)
            self.model = model
            self.alpha = float(payload.get("alpha", self.alpha))


def _patch_and_reward(transition: Any) -> tuple[Patch | None, float | None]:
    if isinstance(transition, dict):
        return transition.get("patch"), transition.get("reward")
    patch = getattr(transition, "selected_patch", None)
    reward_result = getattr(transition, "reward", None)
    reward = getattr(reward_result, "value", reward_result)
    return patch, reward
