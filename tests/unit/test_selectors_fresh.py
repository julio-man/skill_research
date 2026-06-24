from __future__ import annotations

from pathlib import Path

from skill_research.patches.types import Patch, PatchPool
from skill_research.selectors.base import SelectorDecision
from skill_research.selectors.noop import NoOpSelector
from skill_research.selectors.random_selector import RandomSelector
from skill_research.selectors.smallest_patch import SmallestPatchSelector
from skill_research.selectors.support_count import SupportCountSelector


PATCHES = PatchPool([
    Patch("p1", "add_rule", "SKILL.md", None, "append_document", "A", delta_tokens=10, support_count=2),
    Patch("p2", "add_rule", "SKILL.md", None, "append_document", "B", delta_tokens=5, support_count=4),
    Patch("noop", "noop", "SKILL.md", None, "no_op", "", delta_tokens=0, support_count=0),
])


def test_noop_selector_selects_no_patch() -> None:
    decision = NoOpSelector().select({}, PATCHES)
    assert decision == SelectorDecision(action_index=None, patch_id="noop", patch=None, reason="noop")


def test_support_count_selector_selects_highest_support_count() -> None:
    decision = SupportCountSelector().select({}, PATCHES)
    assert decision.patch_id == "p2"


def test_smallest_patch_selector_ignores_noop_by_default() -> None:
    decision = SmallestPatchSelector().select({}, PATCHES)
    assert decision.patch_id == "p2"


def test_random_selector_is_seeded() -> None:
    selector_a = RandomSelector(seed=5)
    selector_b = RandomSelector(seed=5)
    assert selector_a.select({}, PATCHES).patch_id == selector_b.select({}, PATCHES).patch_id


def test_selector_state_hooks_write_json(tmp_path: Path) -> None:
    selector = SupportCountSelector()
    state_path = tmp_path / "state.json"
    selector.observe({"reward": 1.0})
    selector.save_state(state_path)
    selector.load_state(state_path)
    assert state_path.exists()
