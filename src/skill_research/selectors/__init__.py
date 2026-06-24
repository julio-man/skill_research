from skill_research.core.registry import ComponentRegistry
from skill_research.selectors.base import BaseSelector, SelectorDecision
from skill_research.selectors.greedy import GreedySelector
from skill_research.selectors.linear_reward_regressor import LinearRewardRegressorSelector
from skill_research.selectors.linucb import LinUCBSelector
from skill_research.selectors.noop import NoOpSelector
from skill_research.selectors.random_selector import RandomSelector
from skill_research.selectors.smallest_patch import SmallestPatchSelector
from skill_research.selectors.support_count import SupportCountSelector


selector_registry = ComponentRegistry()
selector_registry.register("greedy", lambda **kwargs: GreedySelector())
selector_registry.register("linear_reward_regressor", lambda l2=1.0, **kwargs: LinearRewardRegressorSelector(l2=l2))
selector_registry.register("linucb", lambda alpha=1.0, l2=1.0, **kwargs: LinUCBSelector(alpha=alpha, l2=l2))
selector_registry.register("noop", lambda **kwargs: NoOpSelector())
selector_registry.register("random", lambda seed=42, **kwargs: RandomSelector(seed))
selector_registry.register("support_count", lambda **kwargs: SupportCountSelector())
selector_registry.register("smallest_patch", lambda **kwargs: SmallestPatchSelector())


def build_selector(name: str, **kwargs):
    return selector_registry.build(name, **kwargs)


__all__ = [
    "BaseSelector",
    "GreedySelector",
    "LinearRewardRegressorSelector",
    "LinUCBSelector",
    "NoOpSelector",
    "RandomSelector",
    "SelectorDecision",
    "SmallestPatchSelector",
    "SupportCountSelector",
    "build_selector",
    "selector_registry",
]
