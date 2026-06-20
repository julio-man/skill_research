from __future__ import annotations

from pathlib import Path
import shutil

from skill_research.data.types import SpreadsheetTask
from skill_research.datasets.spreadsheetbench_verified import load_dataset
from skill_research.evaluation.base import CheckResult, EvaluationResult
from skill_research.evaluation.spreadsheet import SpreadsheetTaskEvaluator


DATASET_ROOT = Path("data/spreadsheetbench_verified/spreadsheetbench_verified_400")


def _task_379_36() -> SpreadsheetTask:
    tasks = load_dataset(DATASET_ROOT)
    return next(task for task in tasks if task.task_id == "379-36")


def test_spreadsheet_evaluator_passes_when_candidate_matches_golden(tmp_path: Path) -> None:
    task = _task_379_36()
    candidate = tmp_path / "candidate.xlsx"
    shutil.copy(task.golden_workbook_path, candidate)

    result = SpreadsheetTaskEvaluator().evaluate(task, candidate)

    assert isinstance(result, EvaluationResult)
    assert result.passed is True
    assert result.score == 1.0
    assert result.failure_type == "none"
    assert all(isinstance(check, CheckResult) for check in result.checks)


def test_spreadsheet_evaluator_fails_when_candidate_is_initial_workbook(tmp_path: Path) -> None:
    task = _task_379_36()
    candidate = tmp_path / "candidate.xlsx"
    shutil.copy(task.initial_workbook_path, candidate)

    result = SpreadsheetTaskEvaluator().evaluate(task, candidate)

    assert result.passed is False
    assert result.score == 0.0
    assert result.failure_type == "wrong_answer"
    assert any(not check.passed for check in result.checks)


def test_spreadsheet_evaluator_fails_when_candidate_missing(tmp_path: Path) -> None:
    task = _task_379_36()
    candidate = tmp_path / "missing.xlsx"

    result = SpreadsheetTaskEvaluator().evaluate(task, candidate)

    assert result.passed is False
    assert result.score == 0.0
    assert result.failure_type == "artifact_missing"
    assert result.checks[0].kind == "artifact_exists"


def test_spreadsheet_evaluator_reports_region_context_in_metadata(tmp_path: Path) -> None:
    task = _task_379_36()
    candidate = tmp_path / "candidate.xlsx"
    shutil.copy(task.golden_workbook_path, candidate)

    result = SpreadsheetTaskEvaluator().evaluate(task, candidate)

    assert result.metadata["task_id"] == "379-36"
    assert result.metadata["answer_region_raw"] == "'Sheet1'!E2:E17"
    assert "expected_region_values" in result.metadata
    assert "actual_region_values" in result.metadata
    assert result.metadata["expected_region_values"]["Sheet1!E10"] == "Georgia WH Tax"
    assert result.metadata["actual_region_values"]["Sheet1!E10"] == "Georgia WH Tax"


def test_spreadsheet_evaluator_includes_expected_and_actual_region_values_on_failure(tmp_path: Path) -> None:
    task = _task_379_36()
    candidate = tmp_path / "candidate.xlsx"
    shutil.copy(task.initial_workbook_path, candidate)

    result = SpreadsheetTaskEvaluator().evaluate(task, candidate)

    assert result.metadata["expected_region_values"]["Sheet1!E10"] == "Georgia WH Tax"
    assert result.metadata["actual_region_values"]["Sheet1!E10"] == "Georgia Its Tax/ga Tx *****0"
