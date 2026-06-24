from __future__ import annotations

import json
from pathlib import Path

from skill_research.reports.generator import generate_report


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generate_report_writes_aggregated_final_test_table_png_only(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "selector_comparison.json", {"selectors": {"random": {"seeds": {"1": {"round_rewards": [0.5], "cumulative_reward": [0.5]}}}}})
    _write(root / "selectors" / "random" / "seed_001" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 2, "avg_score": 0.5, "pass_rate": 0.5, "failure_histogram": {"none": 1, "wrong_answer": 1}})

    generate_report(root, tmp_path / "reports")

    assert (tmp_path / "reports" / "table_pngs" / "selector_final_summary.png").exists()
    assert not (tmp_path / "reports" / "table_pngs" / "final_test_scores.png").exists()
    assert not (tmp_path / "reports" / "table_pngs" / "per_round_rewards.png").exists()
    assert not (tmp_path / "reports" / "table_pngs" / "selected_patches.png").exists()
