from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook

from skill_research.core.types import Task
from skill_research.evaluators.spreadsheet import SpreadsheetEvaluator, answer_cell_refs


def _save(path: Path, cells: dict[str, object]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    for cell, value in cells.items():
        ws[cell] = value
    wb.save(path)


def test_answer_cell_refs_expands_answer_position_with_answer_sheet() -> None:
    task = Task("t1", "x", metadata={"answer_position": "A1:B2", "answer_sheet": "Sheet1"})

    assert answer_cell_refs(task) == ["Sheet1!A1", "Sheet1!B1", "Sheet1!A2", "Sheet1!B2"]


def test_spreadsheet_evaluator_scores_range_cells(tmp_path: Path) -> None:
    candidate = tmp_path / "candidate.xlsx"
    golden = tmp_path / "golden.xlsx"
    _save(candidate, {"A1": 1, "B1": 2, "A2": 3, "B2": 9})
    _save(golden, {"A1": 1, "B1": 2, "A2": 3, "B2": 4})
    task = Task("t1", "x", metadata={"golden_workbook_path": str(golden), "answer_position": "A1:B2", "answer_sheet": "Sheet1"})

    result = SpreadsheetEvaluator().evaluate(task, {"artifact_path": str(candidate)})

    assert result.passed is False
    assert result.score == 0.75
    assert result.failure_type == "wrong_answer"
