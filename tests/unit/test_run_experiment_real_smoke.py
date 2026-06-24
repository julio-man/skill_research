from __future__ import annotations

import json
from pathlib import Path

from skill_research.cli.run_experiment import main


def test_run_experiment_executes_multiseed_multiround_smoke_with_replay_llms(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Spreadsheet Skill\nCopy the workbook for this smoke test.\n", encoding="utf-8")
    output_dir = tmp_path / "runs"
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "experiment_id": "smoke",
                "dataset": {
                    "name": "spreadsheetbench_verified",
                    "split": "val",
                    "root": "data/spreadsheetbench_verified/spreadsheetbench_verified_400",
                    "limit": 1,
                    "seed": 1,
                },
                "skill": {"path": str(skill_dir)},
                "executor": {
                    "name": "spreadsheet_python",
                    "llm": {
                        "name": "replay",
                        "responses": ["from openpyxl import load_workbook\nwb = load_workbook(INPUT_WORKBOOK)\nwb.save(OUTPUT_WORKBOOK)\n"] * 12,
                    },
                    "temperature": 0.0,
                    "max_tokens": 200,
                },
                "evaluator": {"name": "spreadsheet"},
                "proposer": {
                    "name": "openai_trace",
                    "llm": {
                        "name": "replay",
                        "responses": ['{"patches": [{"patch_id": "noop", "patch_type": "noop", "target_file": "SKILL.md", "target_section": null, "operation": "no_op", "content": "", "supported_trace_ids": []}]}'] * 2,
                    },
                },
                "applier": {"name": "skill_directory"},
                "reward": {"name": "score_delta"},
                "selectors": [{"name": "noop"}],
                "run": {"rounds": 1, "seeds": [1, 2], "output_dir": str(output_dir)},
            }
        ),
        encoding="utf-8",
    )

    main(["--config", str(spec_path)])

    comparison = json.loads((output_dir / "selector_comparison.json").read_text(encoding="utf-8"))
    assert sorted(comparison["selectors"]["noop"]["seeds"]) == ["1", "2"]
    assert len(comparison["selectors"]["noop"]["seeds"]["1"]["cumulative_reward"]) == 1
    assert (output_dir / "selectors" / "noop" / "seed_001" / "round_000" / "episode.json").exists()
