"""Reward function that penalizes token growth and anchor regressions."""

from __future__ import annotations

from skill_research.rewards.base import RewardResult


class BloatRegressionReward:
    name = "bloat_regression"

    def __init__(self, lambda_token_growth: float = 0.0, mu_anchor_regression: float = 0.0):
        self.lambda_token_growth = lambda_token_growth
        self.mu_anchor_regression = mu_anchor_regression

    def compute(self, before, after, context: dict | None = None) -> RewardResult:
        context = context or {}
        score_delta = round(float(after.avg_score) - float(before.avg_score), 10)
        pass_rate_delta = round(float(after.pass_rate) - float(before.pass_rate), 10)
        token_growth = int(context.get("token_growth", 0))
        anchor_regressions = int(context.get("anchor_regressions", 0))
        value = round(score_delta - self.lambda_token_growth * token_growth - self.mu_anchor_regression * anchor_regressions, 10)
        return RewardResult(
            value=value,
            score_delta=score_delta,
            pass_rate_delta=pass_rate_delta,
            token_growth=token_growth,
            anchor_regressions=anchor_regressions,
            metadata={"lambda_token_growth": self.lambda_token_growth, "mu_anchor_regression": self.mu_anchor_regression},
        )
