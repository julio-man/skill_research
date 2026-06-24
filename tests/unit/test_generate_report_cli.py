from __future__ import annotations

import json
from pathlib import Path

from skill_research.cli.generate_report import main


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_generate_report_cli_writes_summary_and_final_tables(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "selector_comparison.json", {"selectors": {"noop": {"seeds": {"1": {"round_rewards": [0.0], "cumulative_reward": [0.0]}}}}})
    _write(root / "selectors" / "noop" / "seed_001" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 1, "avg_score": 0.0, "pass_rate": 0.0, "failure_histogram": {"wrong_answer": 1}})
    out = tmp_path / "reports"

    main(["--run-root", str(root), "--output-dir", str(out)])

    assert (out / "summary.md").exists()
    assert (out / "tables" / "selector_final_summary.csv").exists()
    assert (out / "table_pngs" / "selector_final_summary.png").exists()
