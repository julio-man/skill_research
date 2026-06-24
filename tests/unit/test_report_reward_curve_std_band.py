from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from skill_research.reports.generator import generate_report


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_reward_curve_figures_support_multiple_seed_variance(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "selector_comparison.json", {"selectors": {"linucb": {"seeds": {"1": {"round_rewards": [0.1, 0.1], "cumulative_reward": [0.1, 0.2]}, "2": {"round_rewards": [-0.1, 0.0], "cumulative_reward": [-0.1, -0.1]}}}}})
    _write(root / "selectors" / "linucb" / "seed_001" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 2, "avg_score": 0.5, "pass_rate": 0.5, "failure_histogram": {"none": 1, "wrong_answer": 1}})
    _write(root / "selectors" / "linucb" / "seed_002" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 2, "avg_score": 0.0, "pass_rate": 0.0, "failure_histogram": {"wrong_answer": 2}})

    generate_report(root, tmp_path / "reports")

    cumulative = Image.open(tmp_path / "reports" / "figures" / "cumulative_reward_curve.png")
    round_reward = Image.open(tmp_path / "reports" / "figures" / "round_reward_curve.png")
    assert cumulative.width >= 1200
    assert round_reward.width >= 1200
