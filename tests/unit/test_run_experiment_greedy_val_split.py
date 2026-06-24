from __future__ import annotations

import json
from pathlib import Path

from skill_research.cli.run_experiment import main


def test_run_experiment_greedy_selector_gets_validation_artifacts(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    out = tmp_path / "out"
    response = '{"patches": [{"patch_id": "p1", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "content": "Rule", "supported_trace_ids": []}]}'
    spec = {
        "experiment_id": "greedy_val",
        "dataset": {"name": "spreadsheetbench_verified", "split": "trace", "root": "data/spreadsheetbench_verified/spreadsheetbench_verified_400", "split_strategy": "stratified", "split_seed": 42, "split_sizes": {"trace": 2, "val": 2, "test": 2}, "stratify_by": "instruction_type", "validation_split": "val", "test_split": "test"},
        "skill": {"path": str(skill)},
        "executor": {"name": "spreadsheet_python", "llm": {"name": "replay", "responses": ["from openpyxl import load_workbook\nwb = load_workbook(INPUT_WORKBOOK)\nwb.save(OUTPUT_WORKBOOK)\n"] * 10}},
        "evaluator": {"name": "spreadsheet"},
        "proposer": {"name": "openai_trace", "llm": {"name": "replay", "responses": [response] * 4}},
        "applier": {"name": "skill_directory"},
        "reward": {"name": "score_delta"},
        "selectors": [{"name": "greedy"}],
        "run": {"rounds": 1, "seeds": [1], "output_dir": str(out)}
    }
    config = tmp_path / "experiment_config.json"
    config.write_text(json.dumps(spec), encoding="utf-8")

    main(["--config", str(config)])

    round_dir = out / "selectors" / "greedy" / "seed_001" / "round_000"
    assert not (round_dir / "trace_eval").exists()
    assert (round_dir / "selector_validation" / "p1" / "evaluation_summary.json").exists()
    assert (out / "selectors" / "greedy" / "seed_001" / "final_test_eval" / "evaluation_summary.json").exists()
