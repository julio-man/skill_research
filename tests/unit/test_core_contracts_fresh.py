from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest

from skill_research.core.registry import ComponentRegistry
from skill_research.core.serialization import from_json_file, to_json_file, to_json_safe
from skill_research.core.types import BenchmarkSummary, SkillRef, Task, TaskSplit
from skill_research.patches.types import Patch


@dataclass
class Nested:
    value: int
    path: Path


def test_core_dataclasses_capture_shared_harness_language(tmp_path: Path) -> None:
    task = Task(task_id="t1", instruction="Do it", input_path=tmp_path / "input", metadata={"family": "toy"})
    skill = SkillRef(path=tmp_path / "skill", skill_id="seed")
    summary = BenchmarkSummary(num_tasks=2, avg_score=0.5, pass_rate=0.25, failure_histogram={"wrong_answer": 1})
    split = TaskSplit(name="val", tasks=[task])
    patch = Patch("p1", "add_rule", "SKILL.md", None, "append_document", "Rule", 4, 2)

    assert task.task_id == "t1"
    assert skill.skill_id == "seed"
    assert summary.failure_histogram["wrong_answer"] == 1
    assert split.tasks == [task]
    assert patch.patch_id == "p1"


def test_component_registry_registers_builds_and_rejects_duplicates() -> None:
    registry = ComponentRegistry[str]()
    registry.register("x", lambda suffix="": f"built{suffix}")

    assert registry.names() == ["x"]
    assert registry.build("x", suffix="!") == "built!"
    with pytest.raises(ValueError, match="already registered"):
        registry.register("x", lambda: "other")
    with pytest.raises(KeyError, match="Unknown component"):
        registry.build("missing")


def test_json_serialization_handles_dataclasses_and_paths(tmp_path: Path) -> None:
    payload = {"nested": Nested(3, tmp_path / "file.txt")}
    output = tmp_path / "out.json"

    assert to_json_safe(payload)["nested"]["path"] == str(tmp_path / "file.txt")
    to_json_file(payload, output)

    loaded = from_json_file(output)
    assert loaded["nested"]["value"] == 3
    assert loaded["nested"]["path"] == str(tmp_path / "file.txt")
