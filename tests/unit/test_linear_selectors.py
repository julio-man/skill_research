from __future__ import annotations

from pathlib import Path

from skill_research.patches.types import Patch, PatchPool
from skill_research.selectors import build_selector, selector_registry
from skill_research.selectors.linear_reward_regressor import LinearRewardRegressorSelector
from skill_research.selectors.linucb import LinUCBSelector


def _pool() -> PatchPool:
    return PatchPool([
        Patch("small", "guidance", "SKILL.md", None, "append_document", "short", delta_tokens=2, support_count=1),
        Patch("supported", "guidance", "SKILL.md", None, "append_document", "longer text", delta_tokens=5, support_count=5),
    ])


def test_linucb_explores_then_updates_toward_observed_reward(tmp_path: Path) -> None:
    selector = LinUCBSelector(alpha=0.0, l2=1.0)
    pool = _pool()

    first = selector.select({}, pool)
    selector.observe({"patch": pool.patches[1], "reward": 1.0})
    second = selector.select({}, pool)

    assert first.patch_id in {"small", "supported"}
    assert second.patch_id == "supported"
    state_path = tmp_path / "linucb.json"
    selector.save_state(state_path)
    restored = LinUCBSelector(alpha=0.0, l2=1.0)
    restored.load_state(state_path)
    assert restored.select({}, pool).patch_id == "supported"


def test_linear_reward_regressor_learns_from_observed_patch_rewards(tmp_path: Path) -> None:
    selector = LinearRewardRegressorSelector(l2=1.0)
    pool = _pool()

    selector.observe({"patch": pool.patches[0], "reward": -1.0})
    selector.observe({"patch": pool.patches[1], "reward": 2.0})

    decision = selector.select({}, pool)
    assert decision.patch_id == "supported"
    assert decision.scores["supported"] > decision.scores["small"]
    state_path = tmp_path / "regressor.json"
    selector.save_state(state_path)
    restored = LinearRewardRegressorSelector(l2=1.0)
    restored.load_state(state_path)
    assert restored.select({}, pool).patch_id == "supported"


def test_linear_selectors_are_registered() -> None:
    assert "linucb" in selector_registry.names()
    assert "linear_reward_regressor" in selector_registry.names()
    assert build_selector("linucb").name == "linucb"
    assert build_selector("linear_reward_regressor").name == "linear_reward_regressor"
