from skill_research.core.registry import ComponentRegistry
from skill_research.rewards.base import RewardFunction, RewardResult
from skill_research.rewards.bloat_regression import BloatRegressionReward
from skill_research.rewards.score_delta import ScoreDeltaReward

reward_registry = ComponentRegistry()
reward_registry.register("score_delta", lambda **kwargs: ScoreDeltaReward())
reward_registry.register("bloat_regression", lambda **kwargs: BloatRegressionReward(**kwargs))


def build_reward(name: str, **kwargs):
    return reward_registry.build(name, **kwargs)


__all__ = ["BloatRegressionReward", "RewardFunction", "RewardResult", "ScoreDeltaReward", "build_reward", "reward_registry"]
