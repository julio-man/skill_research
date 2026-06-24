from __future__ import annotations

from skill_research.patches.types import Patch, PatchPool
from skill_research.selectors.noop import NoOpSelector


def test_noop_selector_selects_no_patch_without_requiring_noop_in_pool() -> None:
    pool = PatchPool([Patch("p1", "guidance", "SKILL.md", None, "append_document", "Rule")])

    decision = NoOpSelector().select({}, pool)

    assert decision.patch is None
    assert decision.patch_id == "noop"
    assert decision.action_index is None
