from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from skill_research.core.types import SkillRef, Task
from skill_research.evaluators.spreadsheet import SpreadsheetEvaluator
from skill_research.executors.spreadsheet_python import SpreadsheetPythonExecutor


class EmptyBackend:
    def complete(self, request):
        return ""


def test_spreadsheet_executor_marks_empty_model_output_without_running_prelude(tmp_path: Path) -> None:
    workbook = tmp_path / "input.xlsx"
    Workbook().save(workbook)
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")

    result = SpreadsheetPythonExecutor(EmptyBackend()).run(Task("t1", "copy", workbook), SkillRef(skill), tmp_path / "out", {})

    assert result.returncode == -2
    assert result.stderr == "empty_model_output"
    assert not Path(result.artifact_path).exists()


def test_spreadsheet_evaluator_reports_empty_model_output_as_failure_type(tmp_path: Path) -> None:
    golden = tmp_path / "golden.xlsx"
    Workbook().save(golden)
    task = Task("t1", "copy", metadata={"golden_workbook_path": str(golden), "answer_cells": ["Sheet1!A1"]})
    execution = {"artifact_path": str(tmp_path / "missing.xlsx"), "returncode": -2, "stderr": "empty_model_output"}

    result = SpreadsheetEvaluator().evaluate(task, execution)

    assert result.failure_type == "empty_model_output"
