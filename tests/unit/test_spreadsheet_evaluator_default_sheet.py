from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from skill_research.core.types import Task
from skill_research.evaluators.spreadsheet import SpreadsheetEvaluator


def _save(path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Active"
    ws["F6"] = 1
    wb.save(path)


def test_spreadsheet_evaluator_uses_golden_active_sheet_when_answer_sheet_missing(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.xlsx"
    golden = tmp_path / "golden.xlsx"
    _save(candidate)
    _save(golden)
    task = Task("t1", "x", metadata={"golden_workbook_path": str(golden), "answer_position": "F6:F6"})

    result = SpreadsheetEvaluator().evaluate(task, {"artifact_path": str(candidate)})

    assert result.passed is True
    assert result.score == 1.0
