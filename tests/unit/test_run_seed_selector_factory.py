from __future__ import annotations

import json
from pathlib import Path

from skill_research.cli.run_experiment import main


def test_run_experiment_random_selector_uses_run_seed_when_seed_omitted(tmp_path: Path) -> None:
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    response = '{"patches": [{"patch_id": "a", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "content": "A", "supported_trace_ids": []}, {"patch_id": "b", "patch_type": "guidance", "target_file": "SKILL.md", "target_section": null, "operation": "append_document", "content": "B", "supported_trace_ids": []}]}'
    config = {
        "experiment_id": "seeded_random",
        "dataset": {"name": "spreadsheetbench_verified", "split": "trace", "root": "data/spreadsheetbench_verified/spreadsheetbench_verified_400", "split_strategy": "stratified", "split_seed": 42, "split_sizes": {"trace": 1, "val": 1, "test": 1}, "stratify_by": "instruction_type"},
        "skill": {"path": str(skill)},
        "executor": {"name": "spreadsheet_python", "llm": {"name": "replay", "responses": ["from openpyxl import load_workbook\nwb = load_workbook(INPUT_WORKBOOK)\nwb.save(OUTPUT_WORKBOOK)\n"] * 6}},
        "evaluator": {"name": "spreadsheet"},
        "proposer": {"name": "openai_trace", "llm": {"name": "replay", "responses": [response] * 4}},
        "applier": {"name": "skill_directory"},
        "reward": {"name": "score_delta"},
        "selectors": [{"name": "random"}],
        "run": {"rounds": 1, "seeds": [1, 2], "output_dir": str(tmp_path / "out")},
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")

    main(["--config", str(path)])

    decision_1 = json.loads((tmp_path / "out" / "selectors" / "random" / "seed_001" / "round_000" / "selection" / "decision.json").read_text())
    decision_2 = json.loads((tmp_path / "out" / "selectors" / "random" / "seed_002" / "round_000" / "selection" / "decision.json").read_text())
    assert decision_1["metadata"]["selector_seed"] == 1
    assert decision_2["metadata"]["selector_seed"] == 2
