from __future__ import annotations

import csv
import json
from pathlib import Path

from skill_research.reports.generator import generate_report
from skill_research.reports.loader import load_report_rows


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_report_loader_extracts_curve_patch_failure_and_flip_rows(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    round_dir = root / "selectors" / "random" / "seed_001" / "round_000"
    _write(root / "selector_comparison.json", {"selectors": {"random": {"seeds": {"1": {"round_rewards": [0.5], "cumulative_reward": [0.5]}}}}})
    _write(round_dir / "selection" / "decision.json", {"selector": "random", "patch_id": "p1", "action_index": 0, "reason": "random"})
    _write(round_dir / "patch_proposal" / "patch_pool.json", {"patches": [{"patch_id": "p1", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": None, "operation": "append_document", "content": "Rule", "delta_tokens": 1, "support_count": 2, "metadata": {"supported_trace_ids": ["t1", "t2"]}}], "metadata": {"proposer": "fake"}})
    _write(round_dir / "current_skill_eval" / "evaluation_summary.json", {"num_tasks": 1, "avg_score": 0.0, "pass_rate": 0.0, "failure_histogram": {"wrong_answer": 1}})
    _write(round_dir / "selected_skill_eval" / "evaluation_summary.json", {"num_tasks": 1, "avg_score": 1.0, "pass_rate": 1.0, "failure_histogram": {"none": 1}})
    _write(round_dir / "current_skill_eval" / "task_traces.json", [{"task_id": "t1", "success": False, "failure_type": "wrong_answer", "payload": {"evaluation": {"score": 0.0, "failure_type": "wrong_answer", "passed": False}}}])
    _write(round_dir / "selected_skill_eval" / "task_traces.json", [{"task_id": "t1", "success": True, "failure_type": "none", "payload": {"evaluation": {"score": 1.0, "failure_type": "none", "passed": True}}}])
    _write(root / "selectors" / "random" / "seed_001" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 1, "avg_score": 0.25, "pass_rate": 0.0, "failure_histogram": {"wrong_answer": 1}})

    rows = load_report_rows(root)

    assert rows.per_round_rewards[0]["selector"] == "random"
    assert rows.selected_patches[0]["patch_id"] == "p1"
    assert rows.failure_modes[0]["wrong_answer"] == 1
    assert rows.task_score_flips[0]["score_delta"] == 1.0
    assert rows.final_test_scores[0]["avg_score"] == 0.25


def test_generate_report_writes_aggregated_final_test_csv_and_summary(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "selector_comparison.json", {"selectors": {"random": {"seeds": {"1": {"round_rewards": [0.5], "cumulative_reward": [0.5]}}}}})
    _write(root / "selectors" / "random" / "seed_001" / "final_test_eval" / "evaluation_summary.json", {"num_tasks": 1, "avg_score": 0.25, "pass_rate": 0.0, "failure_histogram": {"wrong_answer": 1}})

    out = tmp_path / "reports"
    generate_report(root, out)

    assert (out / "summary.md").exists()
    assert (out / "tables" / "selector_final_summary.csv").exists()
    assert not (out / "tables" / "final_test_scores.csv").exists()
    assert not (out / "tables" / "per_round_rewards.csv").exists()
    with (out / "tables" / "selector_final_summary.csv").open(newline="", encoding="utf-8") as handle:
        assert list(csv.DictReader(handle))[0]["selector"] == "random"
