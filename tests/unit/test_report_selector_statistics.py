from __future__ import annotations

import csv
import json
from pathlib import Path

from skill_research.reports.generator import generate_report


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_selector_summary_includes_std_auc_and_baseline_deltas(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "selector_comparison.json", {"selectors": {
        "noop": {"seeds": {"1": {"round_rewards": [0.0, 0.0], "cumulative_reward": [0.0, 0.0]}, "2": {"round_rewards": [0.0, 0.0], "cumulative_reward": [0.0, 0.0]}}},
        "random": {"seeds": {"1": {"round_rewards": [0.1, 0.2], "cumulative_reward": [0.1, 0.3]}, "2": {"round_rewards": [0.2, 0.0], "cumulative_reward": [0.2, 0.2]}}},
        "linucb": {"seeds": {"1": {"round_rewards": [0.2, 0.3], "cumulative_reward": [0.2, 0.5]}, "2": {"round_rewards": [0.1, 0.2], "cumulative_reward": [0.1, 0.3]}}}
    }})
    for selector, scores in {"noop": [0.0, 0.0], "random": [0.2, 0.4], "linucb": [0.6, 0.8]}.items():
        for idx, score in enumerate(scores, 1):
            _write(root / "selectors" / selector / f"seed_{idx:03d}" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 2, "avg_score": score, "pass_rate": score, "failure_histogram": {"none": int(score > 0), "wrong_answer": 2 - int(score > 0)}})
    out = tmp_path / "reports"

    generate_report(root, out)

    rows = {row["selector"]: row for row in csv.DictReader((out / "tables" / "selector_final_summary.csv").open(encoding="utf-8"))}
    assert "final_cumulative_reward_std" in rows["linucb"]
    assert "cumulative_reward_auc_mean" in rows["linucb"]
    assert rows["linucb"]["delta_vs_noop_final_reward_mean"] == "0.4"
    assert rows["linucb"]["delta_vs_random_final_reward_mean"] == "0.15"
    assert rows["linucb"]["final_test_avg_score_std"]
