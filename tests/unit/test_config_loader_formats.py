from __future__ import annotations

from pathlib import Path

import pytest

from skill_research.config.loader import load_experiment_spec


SPEC_TOML = '''
experiment_id = "toml-smoke"

[dataset]
name = "spreadsheetbench_verified"
split = "val"
root = "data/spreadsheetbench_verified/spreadsheetbench_verified_400"
limit = 1

[skill]
path = "skill"

[executor]
name = "spreadsheet_python"

[evaluator]
name = "spreadsheet"

[proposer]
name = "openai_trace"

[applier]
name = "skill_directory"

[reward]
name = "score_delta"

[run]
rounds = 1
seeds = [1]
output_dir = "runs"

[[selectors]]
name = "noop"
'''


def test_load_experiment_spec_toml(tmp_path: Path) -> None:
    path = tmp_path / "spec.toml"
    path.write_text(SPEC_TOML, encoding="utf-8")

    spec = load_experiment_spec(path)

    assert spec.experiment_id == "toml-smoke"
    assert spec.dataset.params["limit"] == 1
    assert spec.selectors[0].name == "noop"


def test_load_experiment_spec_yaml_reports_missing_dependency(tmp_path: Path) -> None:
    path = tmp_path / "spec.yaml"
    path.write_text("experiment_id: x\n", encoding="utf-8")

    with pytest.raises(ValueError, match="YAML"):
        load_experiment_spec(path)
