from __future__ import annotations

from skill_research.rewards.base import RewardResult


class ScoreDeltaReward:
    name = "score_delta"

    def compute(self, before, after, context: dict | None = None) -> RewardResult:
        score_delta = round(float(after.avg_score) - float(before.avg_score), 10)
        pass_rate_delta = round(float(after.pass_rate) - float(before.pass_rate), 10)
        return RewardResult(value=score_delta, score_delta=score_delta, pass_rate_delta=pass_rate_delta)
