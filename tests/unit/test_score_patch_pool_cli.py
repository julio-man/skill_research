from __future__ import annotations

import json
from pathlib import Path

from skill_research.cli.score_patch_pool import main
from skill_research.patches.types import Patch, PatchPool


def test_score_patch_pool_cli_scores_saved_pool(tmp_path: Path) -> None:
    skill_dir = tmp_path / "skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    patch_pool_path = tmp_path / "patches.json"
    PatchPool([Patch("noop", "noop", "SKILL.md", None, "no_op", "")]).save(patch_pool_path)
    output_dir = tmp_path / "scores"
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(
        json.dumps(
            {
                "experiment_id": "score",
                "dataset": {"name": "spreadsheetbench_verified", "split": "val", "root": "data/spreadsheetbench_verified/spreadsheetbench_verified_400", "limit": 1},
                "skill": {"path": str(skill_dir)},
                "executor": {"name": "spreadsheet_python", "llm": {"name": "replay", "responses": ["from openpyxl import load_workbook\nwb = load_workbook(INPUT_WORKBOOK)\nwb.save(OUTPUT_WORKBOOK)\n"] * 2}, "temperature": 0.0},
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

    main(["--config", str(spec_path), "--patch-pool", str(patch_pool_path)])

    scores = json.loads((output_dir / "patch_scores.json").read_text(encoding="utf-8"))
    assert scores[0]["patch_id"] == "noop"
    assert "reward" in scores[0]
