from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from skill_research.reports.generator import generate_report


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_report_tables_are_aggregated_final_test_only_and_table_png_is_readable(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "selector_comparison.json", {"selectors": {"random": {"seeds": {"1": {"round_rewards": [0.1, 0.2], "cumulative_reward": [0.1, 0.3]}}}}})
    _write(root / "selectors" / "random" / "seed_001" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 2, "avg_score": 0.5, "pass_rate": 0.5, "failure_histogram": {"none": 1, "wrong_answer": 1}})

    out = tmp_path / "reports"
    generate_report(root, out)

    table_files = sorted(path.name for path in (out / "tables").glob("*.csv"))
    table_pngs = sorted(path.name for path in (out / "table_pngs").glob("*.png"))
    assert table_files == ["selector_final_summary.csv"]
    assert table_pngs == ["selector_final_summary.png"]
    assert (out / "figures" / "cumulative_reward_curve.png").exists()
    assert (out / "figures" / "round_reward_curve.png").exists()
    image = Image.open(out / "table_pngs" / "selector_final_summary.png")
    assert image.width >= 1000
    assert image.height >= 250
