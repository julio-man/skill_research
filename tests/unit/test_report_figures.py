from __future__ import annotations

import json
from pathlib import Path

from skill_research.reports.generator import generate_report


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generate_report_writes_training_curves_and_final_test_failure_figure(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "selector_comparison.json", {"selectors": {"random": {"seeds": {"1": {"round_rewards": [0.1, -0.1], "cumulative_reward": [0.1, 0.0]}}}}})
    _write(root / "selectors" / "random" / "seed_001" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 2, "avg_score": 0.5, "pass_rate": 0.5, "failure_histogram": {"none": 1, "wrong_answer": 1}})

    generate_report(root, tmp_path / "reports")

    assert (tmp_path / "reports" / "figures" / "cumulative_reward_curve.png").exists()
    assert (tmp_path / "reports" / "figures" / "round_reward_curve.png").exists()
    assert (tmp_path / "reports" / "figures" / "final_test_failure_modes.png").exists()
    assert not (tmp_path / "reports" / "figures" / "failure_modes_by_eval.png").exists()
