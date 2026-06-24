from __future__ import annotations

import json
from pathlib import Path

from skill_research.config.loader import load_experiment_spec
from skill_research.datasets.base import InMemoryDatasetProvider
from skill_research.core.types import Task


def test_load_experiment_spec_json(tmp_path: Path) -> None:
    path = tmp_path / "experiment.json"
    path.write_text(
        json.dumps(
            {
                "experiment_id": "exp",
                "dataset": {"name": "memory", "split": "val"},
                "skill": {"path": "skills/seed"},
                "executor": {"name": "exec"},
                "evaluator": {"name": "eval"},
                "proposer": {"name": "prop"},
                "applier": {"name": "apply"},
                "reward": {"name": "score_delta"},
                "selectors": [{"name": "noop"}],
                "run": {"rounds": 1, "seeds": [1], "output_dir": "runs/exp"},
            }
        ),
        encoding="utf-8",
    )
    spec = load_experiment_spec(path)
    assert spec.experiment_id == "exp"
    assert spec.selectors[0].name == "noop"


def test_in_memory_dataset_provider_returns_named_split() -> None:
    task = Task("t1", "Do it")
    provider = InMemoryDatasetProvider({"val": [task]})
    split = provider.load_split("val")
    assert split.name == "val"
    assert split.tasks == [task]
    assert split.dataset.name == "memory"
