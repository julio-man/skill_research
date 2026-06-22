from __future__ import annotations

from skill_research.selectors.heuristic import NoOpSelector, SmallestPatchSelector, SupportCountSelector
from skill_research.selectors.random_selector import RandomSelector


_SELECTOR_BUILDERS = {
    "noop": NoOpSelector,
    "support_count": SupportCountSelector,
    "smallest_patch": SmallestPatchSelector,
    "random": RandomSelector,
}


def build_selector(name: str, seed: int = 42):
    try:
        builder = _SELECTOR_BUILDERS[name]
    except KeyError as error:
        supported = ", ".join(sorted(_SELECTOR_BUILDERS))
        raise ValueError(f"Unknown selector '{name}'. Expected one of: {supported}") from error
    if builder is RandomSelector:
        return builder(seed=seed)
    return builder()


__all__ = [
    "NoOpSelector",
    "RandomSelector",
    "SmallestPatchSelector",
    "SupportCountSelector",
    "build_selector",
]
