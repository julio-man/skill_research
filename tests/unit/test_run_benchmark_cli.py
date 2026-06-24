from __future__ import annotations

import json
from pathlib import Path

from skill_research.cli.run_benchmark import main


def test_run_benchmark_cli_runs_dataset_executor_evaluator(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    output_dir = tmp_path / "benchmark"
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "experiment_id": "bench",
                "dataset": {"name": "spreadsheetbench_verified", "split": "val", "root": "data/spreadsheetbench_verified/spreadsheetbench_verified_400", "limit": 1},
                "skill": {"path": str(skill_dir)},
                "executor": {"name": "spreadsheet_python", "llm": {"name": "replay", "responses": ["from openpyxl import load_workbook\nwb = load_workbook(INPUT_WORKBOOK)\nwb.save(OUTPUT_WORKBOOK)\n"]}, "temperature": 0.0},
                "evaluator": {"name": "spreadsheet"},
                "proposer": {"name": "openai_trace"},
                "applier": {"name": "skill_directory"},
                "reward": {"name": "score_delta"},
                "selectors": [{"name": "noop"}],
                "run": {"rounds": 1, "seeds": [1], "output_dir": str(output_dir)},
            }
        ),
        encoding="utf-8",
    )

    main(["--config", str(spec_path)])

    summary = json.loads((output_dir / "evaluation_summary.json").read_text(encoding="utf-8"))
    assert summary["num_tasks"] == 1
    assert (output_dir / "task_traces.json").exists()
