from __future__ import annotations

import csv
import json
from pathlib import Path

from skill_research.reports.generator import generate_report


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_final_tables_are_aggregated_by_selector_and_figures_are_final_test_focused(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "selector_comparison.json", {"selectors": {"random": {"seeds": {"1": {"round_rewards": [0.1], "cumulative_reward": [0.1]}, "2": {"round_rewards": [0.3], "cumulative_reward": [0.3]}}}}})
    _write(root / "selectors" / "random" / "seed_001" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 2, "avg_score": 0.25, "pass_rate": 0.0, "failure_histogram": {"wrong_answer": 2}})
    _write(root / "selectors" / "random" / "seed_002" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 2, "avg_score": 0.75, "pass_rate": 0.5, "failure_histogram": {"none": 1, "wrong_answer": 1}})

    out = tmp_path / "reports"
    generate_report(root, out)

    table_files = sorted(path.name for path in (out / "tables").glob("*.csv"))
    assert table_files == ["selector_final_summary.csv"]
    rows = list(csv.DictReader((out / "tables" / "selector_final_summary.csv").open(encoding="utf-8")))
    assert len(rows) == 1
    assert rows[0]["selector"] == "random"
    assert rows[0]["seeds"] == "2"
    assert rows[0]["final_test_avg_score_mean"] == "0.5"
    assert rows[0]["final_test_pass_rate_mean"] == "0.25"
    assert rows[0]["wrong_answer_total"] == "3"
    assert rows[0]["none_total"] == "1"
    assert (out / "figures" / "final_test_failure_modes.png").exists()
    assert not (out / "figures" / "failure_modes_by_eval.png").exists()
    assert (out / "table_pngs" / "selector_final_summary.png").exists()
    assert not (out / "table_pngs" / "final_test_scores.png").exists()
