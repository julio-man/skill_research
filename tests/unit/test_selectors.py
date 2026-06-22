from __future__ import annotations

from skill_research.patches.types import Patch
from skill_research.selectors.heuristic import NoOpSelector, SupportCountSelector, SmallestPatchSelector


PATCHES = [
    Patch("p1", "add_rule", "SKILL.md", None, "append_document", "a", 10, 2),
    Patch("p2", "add_checklist", "SKILL.md", None, "append_document", "b", 5, 5),
    Patch("p3", "add_example", "SKILL.md", None, "append_document", "c", 8, 1),
]

NOOP_PATCH = Patch("noop", "noop", "SKILL.md", None, "no_op", "", 0, 0)


def test_noop_selector_returns_noop_patch() -> None:
    selector = NoOpSelector()

    selected = selector.select({}, PATCHES + [NOOP_PATCH])

    assert selected.patch_id == "noop"



def test_support_count_selector_prefers_highest_support_count() -> None:
    selector = SupportCountSelector()

    selected = selector.select({}, PATCHES)

    assert selected.patch_id == "p2"



def test_smallest_patch_selector_prefers_smallest_delta_tokens() -> None:
    selector = SmallestPatchSelector()

    selected = selector.select({}, PATCHES)

    assert selected.patch_id == "p2"
