from __future__ import annotations

from skill_research.patches.types import Patch
from skill_research.selectors.random_selector import RandomSelector


PATCHES = [
    Patch("p1", "add_rule", "SKILL.md", None, "append_document", "a", 10, 2),
    Patch("p2", "add_checklist", "SKILL.md", None, "append_document", "b", 5, 5),
    Patch("p3", "add_example", "SKILL.md", None, "append_document", "c", 8, 1),
]


def test_random_selector_is_seeded_and_repeatable() -> None:
    first = RandomSelector(seed=42).select({}, PATCHES)
    second = RandomSelector(seed=42).select({}, PATCHES)

    assert first.patch_id == second.patch_id


def test_random_selector_uses_seed_in_a_nontrivial_way() -> None:
    first = RandomSelector(seed=42).select({}, PATCHES)
    second = RandomSelector(seed=43).select({}, PATCHES)

    assert first.patch_id != second.patch_id or len({p.patch_id for p in PATCHES}) == 1


def test_random_selector_advances_deterministically_across_multiple_calls() -> None:
    first_selector = RandomSelector(seed=42)
    second_selector = RandomSelector(seed=42)

    first_sequence = [first_selector.select({}, PATCHES).patch_id for _ in range(5)]
    second_sequence = [second_selector.select({}, PATCHES).patch_id for _ in range(5)]

    assert first_sequence == second_sequence
